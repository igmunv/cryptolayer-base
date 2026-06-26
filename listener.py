import threading

import lzma

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import Prehashed
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

import wordcoder
import packet as pckt
import config


class Listener:


    # Ключ шифрования
    aes_key = None

    # Цифровая подпись собеседника
    companion_public_key = None

    # Сессия promt_toolkit для вывода в терминал
    pt_session = None

    # Функция которая будет получать готовые данные
    ready_data_ingester = None

    # Используется ли шифрование
    DO_ENCRYPT = False

    # Используется ли цифровая подпись
    DO_SIGN = False

    # Получен ли NODE ID
    NODE_ID_FLAG = False

    # Получена ли подпись
    EXCHANGE_SIGN_FLAG = False

    # Получен ли ECC public key
    EXCHANGE_PUBLIC_KEY_FLAG = False

    # Потоки байтов которые мы ожидаем
    # ID потока: {count: количество пакетов в данном потоке, packets: [массив полученных пакетов в потоке]}
    WAITING_STREAMS = {}

    DATA_BUFFER = []


    def __init__(self, aes_key, companion_public_key, session, ready_data_ingester):
        self.aes_key = aes_key
        self.companion_public_key = companion_public_key
        self.pt_session = session
        self.ready_data_ingester = ready_data_ingester

        threading.Thread(target=self.data_handler).start()


    def update_aes_key(self, new_aes_key):
        self.aes_key = new_aes_key

    def update_companion_public_key(self, new_companion_public_key):
        self.companion_public_key = new_companion_public_key


    # Она принимает текст из модуля мессенджера
    # Отвечает только за безопасное получение всех пакетов данного стрима
    # Не занимается расшифровкой и распаковкой данных
    def ingester(self, text):

        # текст в массив
        encoded_packet = text.split(" ")

        # декодируем
        wc = wordcoder.WordCoder(config.DICT_WORDCODER_RU)
        raw_packet = wc.decode(encoded_packet)

        if self.DO_SIGN:

            # парсинг подписи
            sig_len = raw_packet[0]
            signature = bytes(raw_packet[1 : 1 + sig_len])
            raw_packet = bytes(raw_packet[1 + sig_len :])

            # проверить подпись
            if not self.check_sign(signature, raw_packet):
                # может потом просто делать return при неправильной подписи
                raise ValueError("sign error") # временно

        # парсинг заголовка пакетаNone
        packet = pckt.Packet.from_bytes(raw_packet)

        # должны принять все чанки данного потока байтов

        # нужно сделать таймер для каждого стрима, чтобы если проходит больше (30 сек * общее кол-во пакетов), и стрим все еще не закончен, то мы его удаляем

        # записываем в ожидаемые стримы
        if packet.stream_id not in self.WAITING_STREAMS:
            self.WAITING_STREAMS[packet.stream_id] = {"count": packet.chunk_count, "pack_type": packet.pack_type, "packets": []}
        self.WAITING_STREAMS[packet.stream_id]["packets"].append({"chunk_id": packet.chunk_id, "payload": packet.payload})
        if self.WAITING_STREAMS[packet.stream_id]["count"] == len(self.WAITING_STREAMS[packet.stream_id]["packets"]):

            # собрать данные в один цельный кусок
            sorted_packets = sorted(self.WAITING_STREAMS[packet.stream_id]["packets"], key=lambda x: x["chunk_id"])
            data = bytes()
            for _packet in sorted_packets:
                data += _packet['payload']

            # передать это куда-то на обработку (например просто положить в массив чтобы второй поток читал его постоянно и обрабатывал пакеты)
            self.DATA_BUFFER.append({"pack_type": self.WAITING_STREAMS[packet.stream_id]["pack_type"], "data": data})

            # удаляем текущий stream
            del self.WAITING_STREAMS[packet.stream_id]


            # ЭТО УДАЛИТЬ
            self.data_handler()


    # Обрабатывает буффер данных
    # Работает во втором потоке
    def data_handler(self):

        while True:
            if self.DATA_BUFFER:

                pack_type = self.DATA_BUFFER[0]['pack_type']
                data = self.DATA_BUFFER[0]['data']
                del self.DATA_BUFFER[0]

                # сначала проверка флагов, на то что у нас передача подписи, node_id или же ecc public_key: DO_ENCRYPT, DO_SIGN
                # и эти флаги будут устанавливаться как нибудь глобальной

                if self.DO_ENCRYPT:

                    nonce = data[:12]
                    encrypted_data = data[12:]

                    aesgcm = AESGCM(self.aes_key)

                    try:
                        data = aesgcm.decrypt(nonce, encrypted_data, associated_data=None)
                    except Exception as e:
                        print("Ошибка дешифрования! Возможно, данные были изменены.")
                        continue

                raw_data = lzma.decompress(data)

                payload_packet = pckt.PayloadPacket.from_bytes(raw_data)

                self.ready_data_ingester(pack_type, payload_packet)


    def check_sign(self, signature, data: bytes) -> bool:
        self.companion_public_key.verify(signature, data, ec.ECDSA(hashes.SHA256()))
        return True # Подпись верна, сообщение подлинноеs
        try:
            self.companion_public_key.verify(signature, data, ec.ECDSA(hashes.SHA256()))
            return True # Подпись верна, сообщение подлинное
        except Exception as e:
            return False # Подпись невалидна!
