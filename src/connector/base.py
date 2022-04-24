import asyncio

from src.common.config import cfg


class Connector:
    def __init__(self):
        # asyncio stream
        self.reader = None
        self.writer = None

        # tasks are created separately, not inside gather, so that they can be canceled later
        self.receiver_task = None
        self.sender_task = None

        # packets
        self.decoder = None
        self.encoder = None
        self.handler = None

        # packet queues
        self.in_queue = asyncio.Queue()
        self.out_queue = asyncio.Queue()

    async def sender(self):
        while not self.writer.is_closing():
            try:
                packet = await self.out_queue.get()
            except asyncio.exceptions.CancelledError:
                break
            self.writer.write(self.encoder.encode(packet))
            await self.writer.drain()
            cfg.logger.debug(f'PACKET SENT: {packet}')

    async def receive(self, size):
        data = await self.reader.read(size)
        packet = self.decoder.decode(data)
        return packet

    async def receiver(self):
        raise NotImplementedError

    async def run(self):
        raise NotImplementedError
