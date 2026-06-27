import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

import threading

from base_module import BaseModule, Credential


class VK(BaseModule):


    name = "VK"
    description = "Russian social network"
    expected_credentials = [Credential("Token", "User Access Token")]

    vk_session = None


    class Sender:



        def __init__(self, credentials, user_id,vk_session):
            self.vk_session = vk_session
            self.user_id = user_id
            self.vk = self.vk_session.get_api()

        def send(self, text: str):
            vk.messages.send(user_id=user_id, message=text, random_id=0)


    class Listener:

        def __init__(self, credentials, ingester: callable, user_id,vk_session):
            self.ingester = ingester
            self.vk_session = vk_session
            self.longpoll = VkLongPoll(vk_session)

        def listen(self) -> str:
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW:
                    if not event.from_me and event.peer_id == self.user_id and event.text:
                        self.ingester(event.text)


    def create_session(self, credentials, ingester: callable, user_id):

        self.vk_session = vk_api.VkApi(token=credentials[0])

        self.listener = self.Listener(credentials, ingester, user_id,vk_session)
        self.sender = self.Sender(credentials, user_id,vk_session)

        threading.Thread(target=listener.listen).start()
