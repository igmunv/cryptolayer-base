
class Credential:


    name = None
    description = None


    def __init__(self, name, desc):
        self.name = name
        self.description = desc


class BaseModule:


    name = None
    description = None
    expected_credentials: list[Credential] = []

    sender = None
    listener = None


    class Sender:

        user_id = None

        def __init__(self, credentials, user_id):
            self.user_id = user_id

        def send(self, text: str):
            pass


    class Listener:


        ingester = None
        user_id = None


        def __init__(self, credentials, ingester: callable, user_id):
            self.ingester = ingester
            self.user_id = user_id

        def listen(self) -> str:
            pass


    def __init_subclass__(cls, **kwargs):

        if not getattr(cls, "expected_credentials", None):
            raise TypeError(f"Class {cls.__name__} must define a unique 'expected_credentials' attribute")
        if not getattr(cls, "name", None):
            raise TypeError(f"Class {cls.__name__} must define a unique 'name' attribute")
        if not getattr(cls, "description", None):
            raise TypeError(f"Class {cls.__name__} must define a unique 'description' attribute")


    def create_session(self, credentials, ingester: callable, user_id):

        self.sender = self.Sender(credentials, user_id)
        self.listener = self.Listener(credentials, ingester, user_id)


    def get_exp_creds(self):
        return self.expected_credentials
