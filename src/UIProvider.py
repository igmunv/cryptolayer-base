from abc import ABC, abstractmethod


# CryptoLayer вызывает методы данного класса для передачи информации в UI
class UIProvider(ABC):

    # Запрос пароля
    @abstractmethod
    def request_password(self, prompt: str) -> str:
        pass

    # Запрос чего-либо. Возвращаемые данные должны соответствовать data_type
    @abstractmethod
    def request_data(self, prompt: str, data_type: type):
        pass

    # Передать в UI текст состояния
    @abstractmethod
    def update_status(self, stage: str, message: str, status_type: str = "in_progress"):
        pass

    # Новое сообщение. Передаем его в UI
    @abstractmethod
    def on_text_received(self, text: str):
        pass

    # Выбор модуля. На основе списка модулей, эллементы которого выглядят как {name: description}
    # необходимо вернуть индекс выбранного модуля
    @abstractmethod
    def select_module(self, modules: list) -> int:
        pass

    # Получение данных для автризации в модуле (мессенджере).
    # Передается список данных для авторизации в виде {name: description}
    # Необходимо вернуть список данных для автризации, где индекс соответствует данным списка credentials
    @abstractmethod
    def get_credentials(self, credentials: list) -> list:
        pass

    # Проверка подписей на правильность
    # Возвращает True ДА или False НЕТ
    @abstractmethod
    def check_signatures(self, my_sign: str, companion_sign: str) -> bool:
        pass

    # Настроен и готов к получению и передаче сообщений
    @abstractmethod
    def on_ready(self):
        pass

    # Таймаут при пинге
    @abstractmethod
    def on_ping_timeout(self):
        pass
