from levels.base import Base
import wordcoder
import config


class Transitional(Base):


    DO_SIGN = False
    SIGN_PRIVATE_KEY = None
    COMPANION_SIGN_PUBLIC_KEY = None
    MODULE_SEND = None


    # постоянно читает данные из PENDING_PROCESSING_BUF и обрабатывает их и отправляет выше
    def receiver(self):
        while True:
            if self.PENDING_PROCESSING_BUF:

                text = self.PENDING_PROCESSING_BUF[0]

                with self.PEND_PROC_BUF_LOCK:
                    del self.PENDING_PROCESSING_BUF[0]

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

                self.UPPER_LEVEL.receive(raw_packet)


    # постоянно читает PENDING_SEND_BUF, формирует пакет и отправляет данные ниже
    def sender(self):
        while True:
            if self.PENDING_SEND_BUF:

                data = self.PENDING_SEND_BUF[0]

                with self.PEND_SEND_BUF_LOCK:
                    del self.PENDING_SEND_BUF[0]

                if DO_SIGN:
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
                self.MODULE_SEND(ready_text)


    def check_sign(self, signature, data: bytes) -> bool:
        try:
            self.COMPANION_SIGN_PUBLIC_KEY.verify(signature, data, ec.ECDSA(hashes.SHA256()))
            return True # Подпись верна, сообщение подлинное
        except Exception as e:
            return False # Подпись невалидна!


