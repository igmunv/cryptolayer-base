import threading
import time
import logging


class Base:

    stop_event = threading.Event()

    def __init__(self):

        # Буффер пришедших данных
        self.PENDING_PROCESSING_BUF = []
        self.PEND_PROC_BUF_LOCK = threading.Lock()

        # Буффер готовых к передаче данных
        self.PENDING_SEND_BUF = []
        self.PEND_SEND_BUF_LOCK = threading.Lock()


        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")


        # запуск 2-х потоков:
        # первый Receiver - читает что в буффере пришло от transitional
        # второй Sender - читает что нужно отправить
        threading.Thread(target=self.sender).start()
        threading.Thread(target=self.receiver).start()


    # Обновить уровни: нижестоящий и вышестоящий
    def update_levels(self, upper_level, lower_level):
        # Класс-Уровень выше
        self.UPPER_LEVEL = upper_level
        # Класс-Уровень ниже
        self.LOWER_LEVEL = lower_level


    # PUBLIC фунция: её вызывает верхний уровень: отправь эти данные
    def send(self, data):
        self.logger.info(f"size: {len(data)}, data: {data}")
        with self.PEND_SEND_BUF_LOCK:
            self.PENDING_SEND_BUF.append(data)


    # PUBLIC фунция: её вызывает нижний уровень: получай эти данные
    def receive(self, data):
        self.logger.info(f"size: {len(data)}, data: {data}")
        with self.PEND_PROC_BUF_LOCK:
            self.PENDING_PROCESSING_BUF.append(data)


    # постоянно читает данные из PENDING_PROCESSING_BUF
    def receiver(self):
        while not self.stop_event.is_set():
            with self.PEND_PROC_BUF_LOCK:
                if self.PENDING_PROCESSING_BUF:
                    data = self.PENDING_PROCESSING_BUF[0]
                    self.logger.info(f"size: {len(data)}, data: {data}")
                    self.rworker(data)
                    del self.PENDING_PROCESSING_BUF[0]
            time.sleep(0.1)


    # обрабатывает данные и отправляет выше
    def rworker(self, data):
        pass


    # постоянно читает PENDING_SEND_BUF
    def sender(self):
        while not self.stop_event.is_set():
            with self.PEND_SEND_BUF_LOCK:
                if self.PENDING_SEND_BUF:
                    data = self.PENDING_SEND_BUF[0]
                    self.logger.info(f"size: {len(data)}, data: {data}")
                    self.sworker(data)
                    del self.PENDING_SEND_BUF[0]
            time.sleep(0.1)

    # формирует пакет и отправляет данные ниже
    def sworker(self, data):
        pass


