import asyncio
import random

from src.common.config import glob
from src.common.commonclasses import Packet
from src.connector.base import WoWConnector
from src.handlers.game import GamePacketHandler


class GameConnector(WoWConnector):

    def __init__(self, discord_queue, *args, **kwargs):
        self.discord_queue = discord_queue
        self.discord_bot = None
        super().__init__(*args, **kwargs)

    def get_handler(self):
        return GamePacketHandler(self.discord_queue, self.out_queue)

    def handle_result(self, result):
        match result:
            case 2:  # World login verified
                self.subtasks.append(asyncio.create_task(self.ping_coroutine(30, 30), name='ping'))
                self.subtasks.append(asyncio.create_task(self.roster_update_coroutine(21, 21), name='roster_update'))
                self.subtasks.append(asyncio.create_task(self.keep_alive_coroutine(5, 30), name='keep_alive'))

    async def ping_coroutine(self, initial_delay, delay):
        glob.logger.debug('Ping coroutine alive')
        ping_id = 1
        data = int.to_bytes(ping_id, 4, 'little') + int.to_bytes(random.randint(0, 50) + 50, 4, 'little')
        try:
            await asyncio.sleep(initial_delay)
        except asyncio.exceptions.CancelledError:
            glob.logger.debug('Ping coroutine canceled before first packet was sent')
            return
        while True:
            try:
                await self.out_queue.put(Packet(glob.codes.client_headers.PING, data))
                glob.logger.debug(f'Sending ping message #{ping_id}')
                ping_id += 1
                await asyncio.sleep(delay)
            except asyncio.exceptions.CancelledError:
                glob.logger.debug('Ping coroutine canceled')
                break

    async def keep_alive_coroutine(self, initial_delay, delay):
        glob.logger.debug('Keep alive coroutine alive')
        try:
            await asyncio.sleep(initial_delay)
        except asyncio.exceptions.CancelledError:
            glob.logger.error('Keep alive coroutine canceled before first packet was sent')
            return
        while True:
            try:
                await self.out_queue.put(Packet(glob.codes.client_headers.KEEP_ALIVE, b''))
                await asyncio.sleep(delay)
            except asyncio.exceptions.CancelledError:
                glob.logger.debug('Keep alive coroutine canceled')
                break

    async def roster_update_coroutine(self, initial_delay, delay):
        glob.logger.debug('Roster update coroutine alive')
        try:
            await asyncio.sleep(initial_delay)
        except asyncio.exceptions.CancelledError:
            glob.logger.debug('Roster update coroutine canceled before first packet was sent')
            return
        while True:
            try:
                self.handler.update_roster()
                await asyncio.sleep(delay)
            except asyncio.exceptions.CancelledError:
                glob.logger.debug('Roster update coroutine canceled')
                break
