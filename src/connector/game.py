import asyncio
import random
import socket

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

    async def run(self):
        glob.logger.info(f'Connecting to game server: {glob.realm.name}')
        try:
            self.reader, self.writer = await asyncio.open_connection(glob.realm.host, glob.realm.port)
        except socket.gaierror:
            glob.logger.critical('Can\'t establish  connection')
            return
        self.tasks.append(asyncio.create_task(self.receiver_coro(), name='Game receiver'))
        self.tasks.append(asyncio.create_task(self.sender_coro(), name='Game sender'))
        self.tasks.append(asyncio.create_task(self.handler_coro(), name='Game handler'))
        try:
            await asyncio.gather(*self.tasks)
        except asyncio.exceptions.CancelledError:
            return

    def handle_result(self, result):
        match result:
            case 1:  # Disconnect
                self.end()
            case 2:  # World login verified
                self.tasks.append(asyncio.create_task(self.ping_coroutine(30, 30), name='ping'))
                self.tasks.append(asyncio.create_task(self.roster_update_coroutine(21, 21), name='roster_update'))
                self.tasks.append(asyncio.create_task(self.keep_alive_coroutine(5, 30), name='keep_alive'))

    async def ping_coroutine(self, initial_delay, delay):
        # glob.logger.debug('Ping coroutine alive')
        ping_id = 1
        latency = random.randint(0, 50) + 50
        data = int.to_bytes(ping_id, 4, 'little') + int.to_bytes(latency, 4, 'little')
        try:
            await asyncio.sleep(initial_delay)
        except asyncio.exceptions.CancelledError:
            glob.logger.debug('Ping coroutine canceled before first packet was sent')
            return
        while not self.writer.is_closing():
            try:
                await self.out_queue.put(Packet(glob.codes.client_headers.PING, data))
                glob.logger.debug(f'Sending ping message #{ping_id}')
                await asyncio.sleep(delay)
            except asyncio.exceptions.CancelledError:
                glob.logger.debug('Ping coroutine canceled')
                break
            ping_id += 1

    async def keep_alive_coroutine(self, initial_delay, delay):
        # glob.logger.debug('Keep alive coroutine alive')
        try:
            await asyncio.sleep(initial_delay)
        except asyncio.exceptions.CancelledError:
            glob.logger.error('Keep alive coroutine canceled before first packet was sent')
            return
        while not self.writer.is_closing():
            try:
                await self.out_queue.put(Packet(glob.codes.client_headers.KEEP_ALIVE, b''))
                await asyncio.sleep(delay)
            except asyncio.exceptions.CancelledError:
                glob.logger.debug('Keep alive coroutine canceled')
                break

    async def roster_update_coroutine(self, initial_delay, delay):
        # glob.logger.debug('Roster update coroutine alive')
        try:
            await asyncio.sleep(initial_delay)
        except asyncio.exceptions.CancelledError:
            glob.logger.debug('Roster update coroutine canceled before first packet was sent')
            return
        while not self.writer.is_closing():
            try:
                self.handler.update_roster()
                await asyncio.sleep(delay)
            except asyncio.exceptions.CancelledError:
                glob.logger.debug('Roster update coroutine canceled')
                break
