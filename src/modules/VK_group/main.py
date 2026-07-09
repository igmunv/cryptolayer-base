import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

import threading, time, logging

from modules.base import BaseModule, Credential


class VK(BaseModule):


    @property
    def name(self): return "VK for groups"

    @property
    def description(self): return "Russian social network. Module for VK-groups"

    expected_credentials = [Credential("Group ID", "Your groud id"), Credential("Token", "Group API Token")]

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

        def __init__(self, credentials, ingester: callable, user_id, vk_session, stop_event, group_id):
            self.group_id = group_id
            self.ingester = ingester
            self.vk_session = vk_session
            self.user_id = user_id
            self.longpoll = VkBotLongPoll(self.vk_session, group_id)
            self.stop_event = stop_event

        def listen(self) -> str:
            while not self.stop_event.is_set():
                for event in self.longpoll.check():
                    if event.type == VkBotEventType.MESSAGE_NEW:

                        message = event.message
                        text = message.get('text')
                        from_id = message.get('from_id')
                        peer_id = message.get('peer_id')

                        if from_id == -self.group_id:
                            continue

                        if peer_id !=  int(self.user_id.strip()):
                            continue

                        # Если вам нужно читать ВСЕ сообщения из беседы:
                        if text:
                            self.ingester(text)


    def create_session(self, ingester: callable):

        self.vk_session = vk_api.VkApi(token=self.credentials[1])

        self.listener = self.Listener(self.credentials, ingester, self.user_id, self.vk_session, self.stop_event, int(self.credentials[0].strip()))
        self.sender = self.Sender(self.credentials, self.user_id, self.vk_session)

        threading.Thread(target=self.listener.listen).start()
