import asyncio
from importlib import import_module

import PyByteBuffer

from src.common.config import glob
from src.encoder import PacketEncoder
from src.decoder import PacketDecoder


class Connector:
    def __init__(self, in_queue, out_queue):
        self.main_task = None
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.handler = self.get_handler()

    def get_handler(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError

    def receiver_coro(self):
        raise NotImplementedError

    def handle_result(self, result):
        pass

    async def handler_coro(self):
        while True:
            try:
                packet = await self.in_queue.get()
            except asyncio.exceptions.CancelledError:
                break
            self.handle_result(self.handler.handle_packet(packet))


class WoWConnector(Connector):
    RECV_SIZE = 8192

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reader = None
        self.writer = None

        self.decoder = PacketDecoder()
        self.encoder = PacketEncoder()
        self.logon_finished = True

    async def sender_coro(self):
        while not self.writer.is_closing():
            try:
                packet = await self.out_queue.get()
                self.writer.write(self.encoder.encode(packet, self.logon_finished))
                await self.writer.drain()
            except asyncio.exceptions.CancelledError:
                break
            # cfg.logger.debug(f'PACKET SENT: {packet}')

    async def receiver_coro(self):
        while not self.writer.is_closing():
            try:
                data = await self.reader.read(WoWConnector.RECV_SIZE)
                if not data:
                    glob.logger.error('Received empty packet')
                    for task in asyncio.all_tasks():
                        task.cancel()
                    self.writer.close()
                if self.decoder.remaining_data:
                    data = self.decoder.remaining_data + data
                buff = PyByteBuffer.ByteBuffer.wrap(data)  # While loop accesses same buffer each time
                while True:
                    packet = self.decoder.decode(buff, self.logon_finished)
                    if packet:
                        # cfg.logger.debug(f'PACKET RECV: {packet}')
                        await self.in_queue.put(packet)
                        if not self.decoder.incomplete_packet:
                            break
                    else:
                        break
            except asyncio.exceptions.CancelledError:
                break
