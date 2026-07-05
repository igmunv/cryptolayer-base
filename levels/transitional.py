from levels.base import Base
import wordcoder
import config
import time

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes


class Transitional(Base):


    DO_SIGN = False
    SIGN_PRIVATE_KEY = None
    COMPANION_SIGN_PUBLIC_KEY = None

    # Класс-Уровень выше
    UPPER_LEVEL = None

    # Класс-Уровень ниже
    LOWER_LEVEL = None


    # постоянно читает данные из PENDING_PROCESSING_BUF и обрабатывает их и отправляет выше
    def rworker(self, data):

        # текст в массив
        encoded_packet = data.split(" ")

        # декодируем
        try:
            wc = wordcoder.WordCoder(config.DICT_WORDCODER_RU)
            data = wc.decode(encoded_packet)
        except Exception as e:
            self.logger.error(f"WordCoder: decode error: {e}")
            return


        # парсинг подписи
        sig_len = data[0]
        signature = bytes(data[1 : 1 + sig_len])
        data = bytes(data[1 + sig_len :])

        # проверить подпись
        if self.DO_SIGN and not self.check_sign(signature, data):
            self.logger.error(f"signature error")
            return

        self.UPPER_LEVEL.receive(data)


    # постоянно читает PENDING_SEND_BUF, формирует пакет и отправляет данные ниже
    def sworker(self, data):

        signature = self.SIGN_PRIVATE_KEY.sign(
            data,
            ec.ECDSA(hashes.SHA256())
        )

        # объединяем (подпись + пакет)
        sig_len = len(signature).to_bytes(1, 'big')
        data = sig_len + signature + data

        # кодирование (ТОЛЬКО ПЕРЕД ОТПРАВКОЙ СООБЩЕНИЯ)
        wc = wordcoder.WordCoder(config.DICT_WORDCODER_RU)
        word_array = wc.encode(data)

        ready_text = " ".join(word_array)
        self.LOWER_LEVEL.send(ready_text)


    def check_sign(self, signature, data: bytes) -> bool:
        try:
            self.COMPANION_SIGN_PUBLIC_KEY.verify(signature, data, ec.ECDSA(hashes.SHA256()))
            return True # Подпись верна, сообщение подлинное
        except Exception as e:
            return False # Подпись невалидна!


