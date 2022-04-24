import asyncio
from importlib import import_module

from src.common.config import cfg
from src.connector.base import Connector


class GameConnector(Connector):

    def __init__(self):
        super().__init__()
        self.decoder = getattr(import_module(f'src.decoder.game.{cfg.expansion}'), 'GamePacketDecoder')()
        self.encoder = getattr(import_module(f'src.encoder.game.{cfg.expansion}'), 'GamePacketEncoder')()
        self.handler = getattr(import_module(f'src.handler.game.{cfg.expansion}'), 'GamePacketHandler')(self.out_queue)

    async def run(self):
        cfg.logger.info(f'Connecting to game server: {cfg.realm["name"]}')
        self.reader, self.writer = await asyncio.open_connection(cfg.realm['host'], cfg.realm['port'])
        self.receiver_task = asyncio.create_task(self.receiver(), name='receiver')
        self.sender_task = asyncio.create_task(self.sender(), name='sender')
        await asyncio.gather(self.receiver_task, self.sender_task)

    async def receiver(self):
        self.handler.handle_packet(await self.receive(64))
        self.handler.handle_packet(await self.receive(100))
        self.writer.close()
        self.sender_task.cancel()
