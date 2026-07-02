import os
import time

import lzma

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from levels.base import Base


class Presentation(Base):


    DO_ENCRYPT = False
    AES_KEY = None


    # постоянно читает данные из PENDING_PROCESSING_BUF и обрабатывает их и отправляет выше
    def receiver(self):
        while True:
            if self.PENDING_PROCESSING_BUF:

                data = self.PENDING_PROCESSING_BUF[0]

                with self.PEND_PROC_BUF_LOCK:
                    del self.PENDING_PROCESSING_BUF[0]

                if self.DO_ENCRYPT:

                    nonce = data[:12]
                    encrypted_data = data[12:]

                    aesgcm = AESGCM(self.AES_KEY)

                    try:
                        data = aesgcm.decrypt(nonce, encrypted_data, associated_data=None)
                    except Exception as e:
                        print("Ошибка дешифрования! Возможно, данные были изменены.")
                        continue

                print("presentation",data, type(data))
                data = lzma.decompress(data)

                self.UPPER_LEVEL.receive(data)
            time.sleep(0.1)


    # постоянно читает PENDING_SEND_BUF, формирует пакет и отправляет данные ниже
    def sender(self):
        while True:
            if self.PENDING_SEND_BUF:

                data = self.PENDING_SEND_BUF[0]

                with self.PEND_SEND_BUF_LOCK:
                    del self.PENDING_SEND_BUF[0]

                # сжатие
                data = lzma.compress(data)

                # шифрование
                if self.DO_ENCRYPT:
                    aesgcm = AESGCM(self.AES_KEY)
                    nonce = os.urandom(12)
                    encrypted_data = aesgcm.encrypt(nonce, data, associated_data=None)
                    data = nonce + encrypted_data

                self.LOWER_LEVEL.send(data)

            time.sleep(0.1)

