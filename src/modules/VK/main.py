import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

import threading, time, logging

from modules.base import BaseModule, Credential


class VK(BaseModule):


    @property
    def name(self): return "VK"

    @property
    def description(self): return "Russian social network"

    expected_credentials = [Credential("Token", "User Access Token")]

    vk_session = None


    class Sender:



        def __init__(self, credentials, user_id,vk_session):
            self.vk_session = vk_session
            self.user_id = user_id
            self.vk = self.vk_session.get_api()
            self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")


        def send(self, text: str):
            try:
                self.vk.messages.send(peer_id=self.user_id, message=text, random_id=0)
            except vk_api.exceptions.Captcha:
                self.logger.error("Captcha needed. Sleep 10 sec...")
                time.sleep(10)
                self.vk.messages.send(peer_id=self.user_id, message=text, random_id=0)
            time.sleep(2)


    class Listener:

        def __init__(self, credentials, ingester: callable, user_id, vk_session, stop_event):
            self.ingester = ingester
            self.vk_session = vk_session
            self.user_id = user_id
            self.longpoll = VkLongPoll(self.vk_session)
            self.stop_event = stop_event

        def listen(self) -> str:
            while not self.stop_event.is_set():
                for event in self.longpoll.check():
                    if event.type == VkEventType.MESSAGE_NEW:
                        if not event.from_me and event.peer_id == int(self.user_id.strip()) and event.text:
                            self.ingester(event.text)


    def create_session(self, credentials, ingester: callable, user_id):

        self.vk_session = vk_api.VkApi(token=self.credentials[0])

        self.listener = self.Listener(self.credentials, ingester, self.user_id, self.vk_session, self.stop_event)
        self.sender = self.Sender(self.credentials, self.user_id, self.vk_session)

        threading.Thread(target=self.listener.listen).start()
