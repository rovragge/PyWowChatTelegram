import asyncio
import socket

import PyByteBuffer

from src.common.config import glob
from src.decoder import PacketDecoder


class Connector:
    def __init__(self, in_queue, out_queue):
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.handler = self.get_handler()

    def get_handler(self):
        raise NotImplementedError

    def receiver_coro(self):
        raise NotImplementedError

    def handle_result(self, result):
        pass

    async def handler_coro(self):
        while True:
            packet = await self.in_queue.get()
            self.handle_result(self.handler.handle_packet(packet))


class WoWConnector(Connector):
    RECV_SIZE = 8192

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reader = None
        self.writer = None
        self.sender_task = None
        self.subtasks = []

        self.decoder = PacketDecoder()
        self.logon_done = True

    async def run(self, address):
        glob.logger.info(f'Connecting to server: {address.host}:{address.port}')
        try:
            self.reader, self.writer = await asyncio.open_connection(address.host, address.port)
        except socket.gaierror:
            glob.logger.error('Can\'t establish connection')
            raise ConnectionAbortedError
        receiver_task = asyncio.create_task(self.receiver_coro(), name='Receiver')
        sender_task = asyncio.create_task(self.sender_coro(), name='Sender')
        handler_task = asyncio.create_task(self.handler_coro(), name='Handler')
        self.subtasks += [receiver_task, sender_task, handler_task]
        await asyncio.gather(receiver_task, sender_task, handler_task)

    async def sender_coro(self):
        while True:
            packet = await self.out_queue.get()
            self.writer.write(self._encode_packet(packet))
            await self.writer.drain()

    async def receiver_coro(self):
        while True:
            data = await self.reader.read(WoWConnector.RECV_SIZE)
            if not data:
                for task in asyncio.all_tasks():
                    if task in self.subtasks:
                        task.cancel()
                raise ConnectionAbortedError
            if self.decoder.remaining_data:
                data = self.decoder.remaining_data + data
            buff = PyByteBuffer.ByteBuffer.wrap(data)  # While loop accesses same buffer each time
            while True:
                packet = self.decoder.decode(buff, self.logon_done)
                if packet:
                    await self.in_queue.put(packet)
                    if not self.decoder.incomplete_packet:
                        break
                else:
                    break

    def _encode_packet(self, packet):
        if not self.logon_done:
            size = 2 if packet.id > 255 else 1
            return int.to_bytes(packet.id, size, 'big') + packet.data
        unencrypted = packet.id == glob.codes.client_headers.AUTH_CHALLENGE
        header_size = 4 if unencrypted else 6
        btarr = bytearray()
        btarr += int.to_bytes(len(packet.data) + header_size - 2, 2, 'big')
        btarr += int.to_bytes(packet.id, 2, 'little')
        header = btarr if unencrypted else glob.crypt.encrypt(btarr + bytearray(2))
        return header + packet.data
