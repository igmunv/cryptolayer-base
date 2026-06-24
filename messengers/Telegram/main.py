from base_module import BaseModule, Credential


class Test(BaseModule):


    name = "Telegram"
    description = "Messenger by Pavel Durov"
    expected_credentials = [Credential("Token", "User Token")]


    class Sender:

        def __init__(self, credentials):
            pass

        def send(self, text: str):
            pass


    class Listener:

        def __init__(self, credentials):
            pass

        def listen(self) -> str:
            pass
