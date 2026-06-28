import os
import time

import lzma

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import Prehashed
from cryptography.hazmat.primitives import serialization

import wordcoder
import packet as pckt
import config
import listener


# Отвечает за отправку данных (но не за мессенджер и его настройки)
class Sender:


    aes_key = None
    private_key = None
    module_send = None

    CURRENT_STREAM_ID = 0

    # !!!! сделать буффер куда кладут данные для отправки, а _send или что-то другое из второго потока берет из буффера и отправляет
    PACKETS_BUFFER = []


    def __init__(self, aes_key, private_key, module_send):
        self.aes_key = aes_key
        self.private_key = private_key
        self.module_send = module_send

    def update_aes_key(self, new_aes_key):
        self.aes_key = new_aes_key

    def update_sign_private_key(self, new_private_key):
        self.private_key = new_private_key

    def send_service(self, cmd_type, data: bytes):
        packet = pckt.PayloadPacket(cmd_type, data).to_bytes()
        self._send(packet, pckt.PackTypes.SERVICE.value)

    def send_comunic(self, data_type, data: bytes):
        packet = pckt.PayloadPacket(data_type, data).to_bytes()
        self._send(packet, pckt.PackTypes.COMMUNIC.value)

    def send_node_id(self, node_id: str):
        packet = pckt.PayloadPacket(pckt.CMDTypes.MY_NODE_ID.value, node_id.encode()).to_bytes()
        self._send(packet, pckt.PackTypes.SERVICE.value, do_encrypt=False, do_sign=False)

    def send_sign(self, sign: bytes):
        packet = pckt.PayloadPacket(pckt.CMDTypes.MY_SIGN.value, sign).to_bytes()
        self._send(packet, pckt.PackTypes.SERVICE.value, do_encrypt=False, do_sign=False)

    def send_public_key(self, public_key: bytes):
        packet = pckt.PayloadPacket(pckt.CMDTypes.MY_PUBLIC_KEY.value, public_key).to_bytes()
        self._send(packet, pckt.PackTypes.SERVICE.value, do_encrypt=False, do_sign=True)

    # Здесь происходит сжатие, шифрование, подпись, кодировка
    # Возращаем уже готовый для отправки массив пакетов
    def data_preparation(self, raw_data: bytes, packet_type, do_encrypt=True):

        # сжатие
        data = lzma.compress(raw_data)

        # шифрование
        if do_encrypt:
            aesgcm = AESGCM(self.aes_key)
            nonce = os.urandom(12)
            encrypted_data = aesgcm.encrypt(nonce, data, associated_data=None)
            data = nonce + encrypted_data


        # разбиваем байты на чанки по config.CHUNK_SIZE байт
        chunks = [data[i:i + config.CHUNK_SIZE] for i in range(0, len(data), config.CHUNK_SIZE)]

        packets = []

        for n, chunk in enumerate(chunks):
            packet = pckt.Packet(packet_type, chunk, len(chunks), self.CURRENT_STREAM_ID, n)
            packets.append(packet)

        self.CURRENT_STREAM_ID = (self.CURRENT_STREAM_ID + 1) % 256

        return packets


    # Подписывает пакет и WordCoder кодирует
    def post_packet_preparation(self, packet: pckt.Packet, do_sign=True) -> str:

        packet.update_time()

        packet = packet.to_bytes()

        if do_sign:
            signature = self.private_key.sign(
                packet,
                ec.ECDSA(hashes.SHA256())
            )

            # объединяем (подпись + пакет)
            sig_len = len(signature).to_bytes(1, 'big')
            packet = sig_len + signature + packet

        # кодирование (ТОЛЬКО ПЕРЕД ОТПРАВКОЙ СООБЩЕНИЯ)
        wc = wordcoder.WordCoder(config.DICT_WORDCODER_RU)
        encoded_packet = wc.encode(packet)

        return encoded_packet



    def _send(self, raw_data, packet_type, do_encrypt=True, do_sign=True):

        #
        #   НУЖНО ОБЯЗАТЕЛЬНО СДЕЛАТЬ ПОДТВЕРЖДЕНИЕ ТОГО ЧТО ПАКЕТ ДОШЕЛ НОРМАЛЬНО.
        #
        #   отправили пакет
        #   сразу ожидаем подтверждение о том что пакет доставлен. в подтверждении будет хеш сумма. сравниваем, если ок то продолжаем
        #   также во время ожидания у нас есть флаг, который означает что мы не можем отправлять пакеты больше, КРОМЕ ПАКЕТОВ ПОДТВЕРЖДЕНИЯ, потому что во время ожидания собеседник может отправить что-либо, и мы должны получить и подтвердить что получили, поэтому флаг этот на отправку подтверждения не действует
        #

        ready_packets = self.data_preparation(raw_data, packet_type, do_encrypt=do_encrypt)
        for n, packet in enumerate(ready_packets):

            word_array = self.post_packet_preparation(packet, do_sign=do_sign)
            ready_text = " ".join(word_array)
            self.module_send(ready_text)

            # хеш подготовить для ожидания подтверждения. так как в подтверждении придет хеш
