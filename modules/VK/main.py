import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

import threading, time

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
            self.vk.messages.send(user_id=self.user_id, message=text, random_id=0)
            time.sleep(1)


    class Listener:

        def __init__(self, credentials, ingester: callable, user_id, vk_session):
            self.ingester = ingester
            self.vk_session = vk_session
            self.user_id = user_id
            self.longpoll = VkLongPoll(self.vk_session)

        def listen(self) -> str:
            while not self.stop_event.is_set():
                for event in self.longpoll.check():
                    if event.type == VkEventType.MESSAGE_NEW:
                        if not event.from_me and event.peer_id == int(self.user_id.strip()) and event.text:
                            self.ingester(event.text)


    def create_session(self, credentials, ingester: callable, user_id):

        self.vk_session = vk_api.VkApi(token=credentials[0])

        self.listener = self.Listener(credentials, ingester, user_id, self.vk_session)
        self.sender = self.Sender(credentials, user_id, self.vk_session)

        threading.Thread(target=self.listener.listen).start()
