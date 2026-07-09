from modules.base import BaseModule, Credential

import time


class Test(BaseModule):


    @property
    def name(self): return "Test"

    @property
    def description(self): return "Module for tests"

    expected_credentials = [Credential("Nothing", "Cred for test")]


    class Sender:

        def __init__(self, credentials, user_id, listener):
            self.listener = listener

        def send(self, text: str):
            # print(text)
            self.listener.listen(text)


    class Listener:

        def __init__(self, credentials, ingester: callable, user_id):
            self.ingester = ingester

        def listen(self, text) -> str:
            self.ingester(text)


    def create_session(self, ingester: callable):
        self.listener = self.Listener(self.credentials, ingester, self.user_id)
        self.sender = self.Sender(self.credentials, self.user_id, self.listener)
