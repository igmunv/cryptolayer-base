import os
import time

import brotli

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from levels.base import Base

import config


class Presentation(Base):


    def __init__(self):
        super().__init__()

        self.DO_ENCRYPT = False
        self.AES_KEY = None


    def compress(self, data):
        return brotli.compress(data, quality=config.COMPRESS_QUALITY)

    def decompress(self, data):
        return brotli.decompress(data)


    # PUBLIC фунция: её вызывает верхний уровень: отправь эти данные БЕЗ ШИФРОВАНИЯ
    def send_without_encrypt(self, data):
        self.logger.info(f"size: {len(data)}")

        data = self.compress(data)

        self.LOWER_LEVEL.send(data)



    # постоянно читает данные из PENDING_PROCESSING_BUF и обрабатывает их и отправляет выше
    def rworker(self, data):
        if self.DO_ENCRYPT:

            nonce = data[:12]
            encrypted_data = data[12:]

            aesgcm = AESGCM(self.AES_KEY)

            try:
                data = aesgcm.decrypt(nonce, encrypted_data, associated_data=None)
            except Exception as e:
                self.logger.error(f"aesgcm decryption error: {e}")
                return

        try:
            data = self.decompress(data)
        except Exception as e:
            self.logger.error(f"decompress error: {e}")
            return

        self.UPPER_LEVEL.receive(data)


    # постоянно читает PENDING_SEND_BUF, формирует пакет и отправляет данные ниже
    def sworker(self, data):

        # сжатие
        data = self.compress(data)

        # шифрование
        if self.DO_ENCRYPT:
            aesgcm = AESGCM(self.AES_KEY)
            nonce = os.urandom(12)
            encrypted_data = aesgcm.encrypt(nonce, data, associated_data=None)
            data = nonce + encrypted_data

        self.LOWER_LEVEL.send(data)

