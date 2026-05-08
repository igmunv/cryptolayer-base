from base_module import BaseModule, Credential


class Test(BaseModule):


    name = "Test"
    description = "Test test test"
    expected_credentials = [Credential("token", "Token token token")]


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
