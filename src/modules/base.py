import threading
import logging
from abc import ABC, abstractmethod


class Credential:


    name = None
    description = None


    def __init__(self, name, desc):
        self.name = name
        self.description = desc


class BaseModule(ABC):


    name: str = None
    description: str = None
    expected_credentials: list[Credential] = []


    @property
    @abstractmethod
    def name(self):
        pass


    @property
    @abstractmethod
    def description(self):
        pass


    class Sender(ABC):


        def __init__(self, credentials, user_id):
            self.user_id = user_id
            self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")


        @abstractmethod
        def send(self, text: str):
            pass


    class Listener(ABC):


        def __init__(self, credentials, ingester: callable, user_id, stop_event):
            self.ingester = ingester
            self.user_id = user_id
            self.stop_event = stop_event
            self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")


        @abstractmethod
        def listen(self) -> str:
            pass


    def __init_subclass__(cls, **kwargs):

        if not getattr(cls, "expected_credentials", None):
            raise TypeError(f"Class {cls.__name__} must define a unique 'expected_credentials' attribute")
        if not getattr(cls, "name", None):
            raise TypeError(f"Class {cls.__name__} must define a unique 'name' attribute")
        if not getattr(cls, "description", None):
            raise TypeError(f"Class {cls.__name__} must define a unique 'description' attribute")


    def __init__(self):
        self.sender = None
        self.listener = None
        self.stop_event = threading.Event()


    # Вызывается только в CryptoLayer
    # Создаёт сессию с использованием Credentials и ID собеседника
    def create_session(self, ingester: callable):
        self.sender = self.Sender(self.credentials, self.user_id)
        self.listener = self.Listener(self.credentials, ingester, self.user_id, self.stop_event)


    def get_creds(self) -> list[dict]:
        ret = []
        for cred in self.expected_credentials:
            ret.append({cred.name: cred.description})
        return ret


    # Не вызывается в CryptoLayer
    # Должен вызываться в приложении до передачи модуля в CryptoLayer
    # Получает необходимые данные для работы модуля
    def init(self, creds: list, user_id: str):
        self.credentials = creds
        self.user_id = user_id

