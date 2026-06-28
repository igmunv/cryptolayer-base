import threading


class Base:


    # Буффер пришедших данных
    PENDING_PROCESSING_BUF = []
    PEND_PROC_BUF_LOCK = threading.Lock()

    # Буффер готовых к передаче данных
    PENDING_SEND_BUF = []
    PEND_SEND_BUF_LOCK = threading.Lock()

    # Класс-Уровень выше
    UPPER_LEVEL = None

    # Класс-Уровень ниже
    LOWER_LEVEL = None


    def __init__(self):

        # запуск 2-х потоков:
        # первый Receiver - читает что в буффере пришло от transitional
        # второй Sender - читает что нужно отправить
        threading.Thread(target=self.sender).start()
        threading.Thread(target=self.receiver).start()


    # PUBLIC фунция: её вызывает верхний уровень: отправь эти данные
    def send(self, data):
        with self.PEND_SEND_BUF_LOCK:
            self.PENDING_SEND_BUF.append(data)


    # PUBLIC фунция: её вызывает нижний уровень: получай эти данные
    def receive(self, data):
        with self.PEND_PROC_BUF_LOCK:
            self.PENDING_PROCESSING_BUF.append(data)


    # постоянно читает данные из PENDING_PROCESSING_BUF и обрабатывает их и отправляет выше
    def receiver(self):
        pass


    # постоянно читает PENDING_SEND_BUF, формирует пакет и отправляет данные ниже
    def sender(self):
        pass


