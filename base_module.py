
class Credential:


    name = None
    description = None


    def __init__(self, name, desc):
        self.name = name
        self.desc = desc


class BaseModule:


    name = None
    description = None
    expected_credentials: list[Credential] = []

    sender = None
    listener = None


    class Sender:

        def __init__(self, credentials):
            pass

        def send(self, text: str):
            pass


    class Listener:


        ingester = None


        def __init__(self, credentials, ingester: callable):
            self.ingester = ingester

        def listen(self) -> str:
            pass


    def __init_subclass__(cls, **kwargs):

        if not getattr(cls, "expected_credentials", None):
            raise TypeError(f"Class {cls.__name__} must define a unique 'expected_credentials' attribute")
        if not getattr(cls, "name", None):
            raise TypeError(f"Class {cls.__name__} must define a unique 'name' attribute")
        if not getattr(cls, "description", None):
            raise TypeError(f"Class {cls.__name__} must define a unique 'description' attribute")


    def create_session(self, credentials, ingester: callable):

        self.sender = self.Sender(credentials)
        self.listener = self.Listener(credentials, ingester)


    def get_exp_creds(self):

        for exp_cred in self.expected_credentials:
            yield exp_cred
