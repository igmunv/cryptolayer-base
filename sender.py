import zstandard as zstd


# Буффер ожидания. Нужен для
WAITING_BUFFER = []


# Отвечает за отправку данных в мессенджер
# Также должен следить за тем чтобы не отправлялось больше 1 сообщения в 2 секунды
class Sender:

    user_id = None
    aes_key = None

    def __init__(self, user_id, aes_key):
        self.user_id = user_id
        self.aes_key = aes_key

    def update_aes_key(self, new_aes_key):
        self.aes_key = new_aes_key

    # Эти функции работают с пакетами
    def send_service(self, cmd_type, data):
        pass

    def send_comunic(self, data_type, data):
        pass

    # Здесь происходит сжатие, шифрование, подпись, кодировка
    def data_preparation(self, raw_data) -> str:

        # сжатие
        cctx = zstd.ZstdCompressor(level=9)
        compressed_data = cctx.compress(raw_data)

        # шифрование

        # подпись

        # кодирование

        pass

    def _send(self, raw_data):
        ready_message = data_preparation(raw_data)
        module.send(ready_message)


# Выполняет роль прослойки между нами и мессенджером
class Messenger:

    # Для общения

    def send_bytes(self):
        pass

    # Служебные

    def ping(self) -> bool:
        pass

    def disconnect(self):
        pass

    def update_keys(self):
        pass

    # Служебные без шифрования

    def send_node_id(self):
        pass

    def send_signature(self):
        pass

    def send_public_key(self):
        pass
