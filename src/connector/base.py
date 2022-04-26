import asyncio

import PyByteBuffer

from src.common.config import cfg


class Connector:
    RECV_SIZE = 8192

    def __init__(self):
        # asyncio stream
        self.reader = None
        self.writer = None

        self.main_task = None

        # packets
        self.decoder = None
        self.encoder = None
        self.handler = None
        # packet queues
        self.in_queue = asyncio.Queue()
        self.out_queue = asyncio.Queue()

    async def run(self):
        raise NotImplementedError

    def handle_result(self, result):
        raise NotImplementedError

    async def sender_coroutine(self):
        while not self.writer.is_closing():
            try:
                packet = await self.out_queue.get()
            except asyncio.exceptions.CancelledError:
                break
            self.writer.write(self.encoder.encode(packet))
            await self.writer.drain()
            cfg.logger.debug(f'PACKET SENT: {packet}')

    async def receiver_coroutine(self):
        while not self.writer.is_closing():
            try:
                data = await self.reader.read(Connector.RECV_SIZE)
                if not data:
                    cfg.logger.error('Received empty packet')
                    raise ValueError
                if self.decoder.remaining_data:
                    data = self.decoder.remaining_data + data
                buff = PyByteBuffer.ByteBuffer.wrap(data)
                while True:
                    packet = self.decoder.decode(buff)
                    if packet:
                        cfg.logger.debug(f'PACKET RECV: {packet}')
                        await self.in_queue.put(packet)
                        if not self.decoder.incomplete_packet:
                            break
                    elif self.decoder.incomplete_packet:
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
