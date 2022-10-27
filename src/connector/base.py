import asyncio
from importlib import import_module

import PyByteBuffer

from src.common.config import glob
from src.encoder import PacketEncoder


class Connector:
    RECV_SIZE = 8192

    def __init__(self):
        self.reader = None
        self.writer = None
        self.main_task = None
        self.in_queue = asyncio.Queue()
        self.out_queue = asyncio.Queue()
        self.discord_queue = asyncio.Queue()

        self.decoder = getattr(import_module(f'src.decoder.{glob.connection_info.expansion}'), 'PacketDecoder')()
        self.encoder = PacketEncoder()
        self.handler = getattr(import_module(f'src.handler.{glob.connection_info.expansion}'), 'PacketHandler')(
            self.out_queue,
            self.discord_queue)
        self.logon_finished = True

    async def run(self):
        raise NotImplementedError

    def handle_result(self, result):
        raise NotImplementedError

    async def sender_coroutine(self):
        while not self.writer.is_closing():
            try:
                packet = await self.out_queue.get()
                self.writer.write(self.encoder.encode(packet, self.logon_finished))
                await self.writer.drain()
            except asyncio.exceptions.CancelledError:
                break
            # cfg.logger.debug(f'PACKET SENT: {packet}')

    async def receiver_coroutine(self):
        while not self.writer.is_closing():
            try:
                data = await self.reader.read(Connector.RECV_SIZE)
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

    async def handler_coroutine(self):
        while not self.writer.is_closing():
            try:
                packet = await self.in_queue.get()
            except asyncio.exceptions.CancelledError:
                break
            result = self.handler.handle_packet(packet)
            self.handle_result(result)
