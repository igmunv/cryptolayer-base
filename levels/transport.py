import threading
import time
import hashlib

from levels.packet import TransportPacket
from levels.base import Base


class Transport(Base):


    # Буффер пришедших данных
    PENDING_PROCESSING_BUF = []
    PEND_PROC_BUF_LOCK = threading.Lock()

    # Буффер готовых к передаче данных
    PENDING_SEND_BUF = []
    PEND_SEND_BUF_LOCK = threading.Lock()

    # Словарь отправленных пакетов, ждущие подтверждения получения
    PENDING_ACK_PACKS = {}
    PENDING_ACK_PACKS_LOCK = threading.Lock()

    # Потоки байтов которые мы ожидаем
    # ID потока: {count: количество пакетов в данном потоке, packets: [массив полученных пакетов в потоке]}
    WAITING_STREAMS = {}

    # Текущий STREAM ID. Нужен для нумерации потоков байт
    CURRENT_STREAM_ID = 0

    # Размер чанков данных в байтах
    CHUNK_SIZE = 100


    # Отправка подтверждения о получении пакета
    def send_acknowledgment(self, rec_raw_packet_bytes):

        hasher = hashlib.sha256()
        hasher.update(rec_raw_packet_bytes)
        packet_hash = hasher.hexdigest()

        packet = TransportPacket(0x1, 0, 0, 0, time.time(), packet_hash.encode())
        raw_packet_bytes = packet.to_bytes()
        self.LOWER_LEVEL.send(raw_packet_bytes)


    # Отправляем пакет и ожидаем подтверждение его получения
    def send_with_pending_acknowledgment(self, raw_packet_bytes, packet_hash):

        with self.PENDING_ACK_PACKS_LOCK:
            self.PENDING_ACK_PACKS[packet_hash] = 0

        self.LOWER_LEVEL.send(raw_packet_bytes)

        while packet_hash in self.PENDING_ACK_PACKS:

            if self.PENDING_ACK_PACKS.get(packet_hash, 0) >= 30:
                self.send_with_pending_acknowledgment(raw_packet_bytes, packet_hash)
                return

            with self.PENDING_ACK_PACKS_LOCK:
                self.PENDING_ACK_PACKS[packet_hash] = self.PENDING_ACK_PACKS[packet_hash] + 1

            time.sleep(1)


    # постоянно читает данные из PENDING_PROCESSING_BUF и обрабатывает их и отправляет выше
    def receiver(self):
        while True:
            if self.PENDING_PROCESSING_BUF:

                raw_packet_bytes = self.PENDING_PROCESSING_BUF[0]

                with self.PEND_PROC_BUF_LOCK:
                    del self.PENDING_PROCESSING_BUF[0]

                packet = TransportPacket.from_bytes(raw_packet_bytes)

                if not packet:
                    continue

                # Проверка на возраст пакета
                difference_seconds = int(time.time()) - packet.time
                # Если пакет старше 5 минут, отбрасываем
                if difference_seconds >= 300:
                    continue

                # Если это пакет подтверждения
                if packet.flags == 0x1:
                    packet_hash = packet.payload.decode()
                    with self.PENDING_ACK_PACKS_LOCK:
                        PENDING_ACK_PACKS.pop(packet_hash, None)

                # Если просто пакет передачи данных
                if packet.flags == 0x0:

                    if packet.stream_id not in self.WAITING_STREAMS:
                        self.WAITING_STREAMS[packet.stream_id] = {"count": packet.chunk_count, "packets": []}
                    self.WAITING_STREAMS[packet.stream_id]["packets"].append({"chunk_id": packet.chunk_id, "payload": packet.payload})

                    if self.WAITING_STREAMS[packet.stream_id]["count"] == len(self.WAITING_STREAMS[packet.stream_id]["packets"]):

                        sorted_packets = sorted(self.WAITING_STREAMS[packet.stream_id]["packets"], key=lambda x: x["chunk_id"])
                        data = bytes()
                        for _packet in sorted_packets:
                            data += _packet['payload']

                        # Передаем выше
                        self.UPPER_LEVEL.receive(data)


    # постоянно читает PENDING_SEND_BUF, формирует пакет и отправляет данные ниже
    def sender(self):
        while True:
            if self.PENDING_SEND_BUF:

                data = self.PENDING_SEND_BUF[0]

                with self.PEND_SEND_BUF_LOCK:
                    del self.PENDING_SEND_BUF[0]

                chunks = [data[i:i + self.CHUNK_SIZE] for i in range(0, len(data), self.CHUNK_SIZE)]

                for n, chunk in enumerate(chunks):

                    packet = TransportPacket(0x0, self.CURRENT_STREAM_ID, len(chunks), n, int(time.time()), chunk)
                    raw_packet_bytes = packet.to_bytes()

                    hasher = hashlib.sha256()
                    hasher.update(raw_packet_bytes)
                    packet_hash = hasher.hexdigest()

                    self.send_with_pending_acknowledgment(raw_packet_bytes, packet_hash)

                self.CURRENT_STREAM_ID = (self.CURRENT_STREAM_ID + 1) % 256



