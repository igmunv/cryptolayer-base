import os
import time

import lzma

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from levels.base import Base


class Presentation(Base):


    DO_ENCRYPT = False
    AES_KEY = None


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
            data = lzma.decompress(data)
        except Exception as e:
            self.logger.error(f"lzma decompress error: {e}")
            return

        self.UPPER_LEVEL.receive(data)


    # постоянно читает PENDING_SEND_BUF, формирует пакет и отправляет данные ниже
    def sworker(self, data):

        # сжатие
        data = lzma.compress(data)

        # шифрование
        if self.DO_ENCRYPT:
            aesgcm = AESGCM(self.AES_KEY)
            nonce = os.urandom(12)
            encrypted_data = aesgcm.encrypt(nonce, data, associated_data=None)
            data = nonce + encrypted_data

        self.LOWER_LEVEL.send(data)

