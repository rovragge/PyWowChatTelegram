import asyncio
import random

from importlib import import_module
from src.common.config import cfg
from src.common.packet import Packet
from src.connector.base import Connector


class GameConnector(Connector):

    def __init__(self):
        super().__init__()
        self.decoder = getattr(import_module(f'src.decoder.game.{cfg.expansion}'), 'GamePacketDecoder')()
        self.encoder = getattr(import_module(f'src.encoder.game.{cfg.expansion}'), 'GamePacketEncoder')()
        self.handler = getattr(import_module(f'src.handler.game.{cfg.expansion}'), 'GamePacketHandler')(self.out_queue)

    async def run(self):
        cfg.logger.info(f'Connecting to game server: {cfg.realm["name"]}')
        cfg.logger.debug(f'Connecting to game server: {cfg.realm["name"]} - {cfg.realm["host"]}:{cfg.realm["port"]}')
        self.reader, self.writer = await asyncio.open_connection(cfg.realm['host'], cfg.realm['port'])
        self.main_task = asyncio.gather(self.receiver_coroutine(), self.sender_coroutine(), self.handler_coroutine())
        try:
            await self.main_task
        except asyncio.exceptions.CancelledError:
            return

    def handle_result(self, result):
        match result:
            case 1:  # Disconnect
                self.writer.close()
                for task in asyncio.all_tasks():
                    task.cancel()
            case 2:  # World login verified
                asyncio.create_task(self.ping_coroutine(30, 30), name='ping')
                asyncio.create_task(self.roster_update_coroutine(61, 61), name='roster_update')
                if cfg.version != 'Vanilla':
                    asyncio.create_task(self.keep_alive_coroutine(15, 30), name='keep_alive')

    async def ping_coroutine(self, initial_delay, delay):
        cfg.logger.debug('Ping coroutine alive')
        ping_id = 0
        latency = random.randint(0, 50) + 90
        data = int.to_bytes(ping_id, 4, 'little') + int.to_bytes(latency, 4, 'little')
        try:
            await asyncio.sleep(initial_delay)
        except asyncio.exceptions.CancelledError:
            cfg.logger.error('Ping coroutine canceled before first packet was sent')
            return
        while not self.writer.is_closing():
            try:
                await self.out_queue.put(Packet(cfg.game_packets.CMSG_PING, data))
                await asyncio.sleep(delay)
            except asyncio.exceptions.CancelledError:
                cfg.logger.error('Ping coroutine canceled')
                break
            ping_id += 1

    async def keep_alive_coroutine(self, initial_delay, delay):
        cfg.logger.debug('Keep alive coroutine alive')
        try:
            await asyncio.sleep(initial_delay)
        except asyncio.exceptions.CancelledError:
            cfg.logger.error('Keep alive coroutine canceled before first packet was sent')
            return
        while not self.writer.is_closing():
            try:
                await self.out_queue.put(Packet(cfg.game_packets.CMSG_KEEP_ALIVE, b''))
                await asyncio.sleep(delay)
            except asyncio.exceptions.CancelledError:
                cfg.logger.error('Keep alive coroutine canceled')
                break

    async def roster_update_coroutine(self, initial_delay, delay):
        cfg.logger.debug('Roster update coroutine alive')
        try:
            await asyncio.sleep(initial_delay)
        except asyncio.exceptions.CancelledError:
            cfg.logger.error('Roster update coroutine canceled before first packet was sent')
            return
        while not self.writer.is_closing():
            try:
                self.handler.update_roster()
                await asyncio.sleep(delay)
            except asyncio.exceptions.CancelledError:
                cfg.logger.error('Roster update coroutine canceled')
                break
