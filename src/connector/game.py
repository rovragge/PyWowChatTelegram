import asyncio
import random
import socket

from src.common.config import glob
from src.common.commonclasses import Packet
from src.connector.base import Connector
from discord_bot import DiscordBot

import discord


class GameConnector(Connector):

    def __init__(self, *args, **kwargs):
        self.discord_bot = None
        super().__init__(*args, **kwargs)

    async def run(self):
        glob.logger.info(f'Connecting to game server: {glob.realm["name"]}')
        try:
            self.reader, self.writer = await asyncio.open_connection(glob.realm['host'], glob.realm['port'])
        except socket.gaierror:
            glob.logger.critical('Can\'t establish  connection')
            return
        self.main_task = asyncio.gather(self.receiver_coroutine(), self.sender_coroutine(), self.handler_coroutine(),
                                        self.discord_receiver_coroutine(), self.discord_writer_coroutine())
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
                asyncio.create_task(self.roster_update_coroutine(21, 21), name='roster_update')
                if glob.connection_info.expansion != 'Vanilla':
                    asyncio.create_task(self.keep_alive_coroutine(15, 30), name='keep_alive')

    async def discord_receiver_coroutine(self):
        self.discord_bot = DiscordBot('.', out_queue=self.out_queue, status=discord.Status.online)
        await self.discord_bot.start(glob.token)

    async def discord_writer_coroutine(self):
        while not self.writer.is_closing() and not self.discord_bot.is_closed():
            if not self.discord_bot.is_ready():
                await asyncio.sleep(1)
                continue
            try:
                packet = await self.discord_queue.get()
            except asyncio.exceptions.CancelledError:
                break
            else:
                if not isinstance(packet, Packet):
                    glob.logger.error('Something other than packet in discord queue!')
                    continue
                self.discord_bot.handle_packet(packet)

    async def ping_coroutine(self, initial_delay, delay):
        glob.logger.debug('Ping coroutine alive')
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
        glob.logger.debug('Keep alive coroutine alive')
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
        glob.logger.debug('Roster update coroutine alive')
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
