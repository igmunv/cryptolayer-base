import os
import time

from levels.packet import ApplicationPacket, PackTypes, DataTypes, CMDTypes, TextMessagePacket

from levels.base import Base


class Application(Base):


    def send_text(self, text: str):
        packet = ApplicationPacket(PackTypes.COMMUNIC.value, DataTypes.TEXT.value, TextMessagePacket(int(time.time()), text.encode()).to_bytes())
        self.send(packet.to_bytes())


    def send_my_node_id(self, node_id: str):
        packet = ApplicationPacket(PackTypes.SERVICE.value, CMDTypes.MY_NODE_ID.value, node_id.encode())
        self.send(packet.to_bytes())


    def send_my_sign(self, sign: bytes):
        packet = ApplicationPacket(PackTypes.SERVICE.value, CMDTypes.MY_SIGN.value, sign)
        self.send(packet.to_bytes())


    def send_my_public_key(self, public_key: bytes):
        packet = ApplicationPacket(PackTypes.SERVICE.value, CMDTypes.MY_PUBLIC_KEY.value, public_key)
        self.LOWER_LEVEL.send_without_encrypt(packet.to_bytes())


    def send_disconnect(self):
        packet = ApplicationPacket(PackTypes.SERVICE.value, CMDTypes.DISCONNECT.value, b'')
        self.send(packet.to_bytes())


    # постоянно читает данные из PENDING_PROCESSING_BUF и обрабатывает их и отправляет выше
    def rworker(self, data):

        packet = ApplicationPacket.from_bytes(data)

        if packet.pack_type == PackTypes.SERVICE.value:

            if packet.data_type == CMDTypes.MY_NODE_ID.value:
                self.UPPER_LEVEL.receive_node_id(packet.payload.decode())

            elif packet.data_type == CMDTypes.MY_SIGN.value:
                self.UPPER_LEVEL.receive_sign(packet.payload)

            elif packet.data_type == CMDTypes.MY_PUBLIC_KEY.value:
                self.UPPER_LEVEL.receive_public_key(packet.payload)

            elif packet.data_type == CMDTypes.DISCONNECT.value:
                self.UPPER_LEVEL.receive_disconnect()

        elif packet.pack_type == PackTypes.COMMUNIC.value:

            if packet.data_type == DataTypes.TEXT.value:
                text_packet = TextMessagePacket.from_bytes(packet.payload)
                self.UPPER_LEVEL.receive_text(text_packet.time, text_packet.payload.decode())


    # постоянно читает PENDING_SEND_BUF, формирует пакет и отправляет данные ниже
    def sworker(self, data):
        self.LOWER_LEVEL.send(data)


