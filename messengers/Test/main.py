from base_module import BaseModule, Credential


class Test(BaseModule):


    name = "Test"
    description = "Virt Messenger for tests"
    expected_credentials = [Credential("Token", "User Token")]


    class Sender:

        def __init__(self, credentials, user_id, listener):
            self.listener = listener

        def send(self, text: str):
            print(text)
            self.listener.listen(text)


    class Listener:

        def __init__(self, credentials, ingester: callable, user_id):
            self.ingester = ingester

        def listen(self, text) -> str:
            self.ingester(text)


    def create_session(self, credentials, ingester: callable, user_id):

        self.listener = self.Listener(credentials, ingester, user_id)
        self.sender = self.Sender(credentials, user_id, self.listener)
