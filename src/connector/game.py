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
        self.pings_done = 0
        super().__init__(*args, **kwargs)

    def get_handler(self):
        return GamePacketHandler(self.discord_queue, self.out_queue)

    def handle_result(self, result):
        match result:
            case 2:  # World login verified
                self.subtasks.append(asyncio.create_task(self.ping_coro(30, 30), name='ping'))
                self.subtasks.append(asyncio.create_task(self.roster_update_coro(21, 21), name='roster_update'))
                self.subtasks.append(asyncio.create_task(self.keep_alive_coro(5, 30), name='keep_alive'))
                self.subtasks.append(asyncio.create_task(self.calendar_coro(30, 30), name='calendar'))

    @staticmethod
    def worker(func):
        async def wrapper(self, initial_delay, delay):
            glob.logger.debug(f'{asyncio.current_task().get_name()} coro alive')
            try:
                await asyncio.sleep(initial_delay)
            except asyncio.exceptions.CancelledError:
                glob.logger.debug(f'{asyncio.current_task().get_name()} coro canceled before first packet was sent')
                return
            while True:
                try:
                    await func(self)
                    await asyncio.sleep(delay)
                except asyncio.exceptions.CancelledError:
                    glob.logger.debug(f'{asyncio.current_task().get_name()} coroutine canceled')
                    return

        return wrapper

    @worker
    async def ping_coro(self):
        self.pings_done += 1
        data = int.to_bytes(self.pings_done, 4, 'little') + int.to_bytes(random.randint(0, 50) + 50, 4, 'little')
        await self.out_queue.put(Packet(glob.codes.client_headers.PING, data))
        glob.logger.debug(f'Sending ping message #{self.pings_done}')

    @worker
    async def keep_alive_coro(self):
        await self.out_queue.put(Packet(glob.codes.client_headers.KEEP_ALIVE, b''))

    @worker
    async def roster_update_coro(self):
        self.handler.update_roster()

    @worker
    async def calendar_coro(self):
        for event_id in glob.calendar.events:
            await self.out_queue.put(
                Packet(glob.codes.client_headers.CALENDAR_GET_EVENT, int.to_bytes(event_id, 8, 'little')))
