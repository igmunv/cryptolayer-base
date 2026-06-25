from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import Prehashed
from cryptography.hazmat.primitives import serialization

import wordcoder
import packet as pckt
import config


class Listener:


    aes_key = None
    companion_public_key = None

    # Потоки байтов которые мы ожидаем
    # ID потока: {count: количество пакетов в данном потоке, packets: [массив полученных пакетов в потоке]}
    WAITING_STREAMS = {}


    def __init__(self, aes_key, companion_public_key):
        self.aes_key = aes_key
        self.companion_public_key = companion_public_key


    # Она принимает текст из модуля мессенджера
    # Отвечает только за безопасное получение всех пакетов данного стрима
    # Не занимается расшифровкой и распаковкой данных
    def ingester(self, text):

        # текст в массив
        encoded_packet = text.split(" ")

        # декодируем
        wc = wordcoder.WordCoder(config.DICT_WORDCODER_RU)
        decoded_packet = wc.decode(encoded_packet)

        # парсинг подписи
        sig_len = decoded_packet[0]
        signature = bytes(decoded_packet[1 : 1 + sig_len])
        raw_packet = bytes(decoded_packet[1 + sig_len :])

        public_bytes = self.companion_public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        public_key_hex = public_bytes.hex()

        # проверить подпись
        if not self.check_sign(signature, raw_packet):
            # может потом просто делать return при неправильной подписи
            raise ValueError("sign error") # временно

        # парсинг заголовка пакета
        packet = pckt.Packet.from_bytes(raw_packet)

        # должны принять все чанки данного потока байтов

        # записываем в ожидаемые стримы
        if packet.stream_id not in self.WAITING_STREAMS:
            self.WAITING_STREAMS[packet.stream_id] = {"count": packet.chunk_count, "pack_type": packet.pack_type, "packets": []}
        self.WAITING_STREAMS[packet.stream_id]["packets"].append({"chunk_id": packet.chunk_id, "payload": packet.payload})
        if self.WAITING_STREAMS[packet.stream_id]["count"] == len(self.WAITING_STREAMS[packet.stream_id]["packets"]):

            # собрать данные в один цельный кусок
            sorted_packets = sorted(self.WAITING_STREAMS[packet.stream_id]["packets"], key=lambda x: x["chunk_id"])
            data = bytes()
            for packet in sorted_packets:
                print("p:", packet)


            # удаляем текущий stream
            # передать это куда-то на обработку (например просто положить в массив чтобы второй поток читал его постоянно и обрабатывал пакеты)


        # уже потом отправляем в data_preparation

        pass


    # Здесь происходит распаковка, расшифровка, проверка подписи, декодировка
    # Возращаем уже готовый для отправки массив пакетов
    def data_preparation(self, encoded_packets, do_encrypt=True, do_sign=True):
        pass


    def check_sign(self, signature, data: bytes) -> bool:
        self.companion_public_key.verify(signature, data, ec.ECDSA(hashes.SHA256()))
        return True # Подпись верна, сообщение подлинноеs
        try:
            self.companion_public_key.verify(signature, data, ec.ECDSA(hashes.SHA256()))
            return True # Подпись верна, сообщение подлинное
        except Exception as e:
            return False # Подпись невалидна!
