import asyncio
import random

from src.common.config import cfg
from src.common.commonclasses import Packet
from src.connector.base import Connector
import socket


class GameConnector(Connector):

    async def run(self):
        cfg.logger.info(f'Connecting to game server: {cfg.realm["name"]}')
        try:
            self.reader, self.writer = await asyncio.open_connection(cfg.realm['host'], cfg.realm['port'])
        except socket.gaierror:
            cfg.logger.critical('Can\'t establish  connection')
            return
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
                if cfg.connection_info.expansion != 'Vanilla':
                    asyncio.create_task(self.keep_alive_coroutine(15, 30), name='keep_alive')

    async def ping_coroutine(self, initial_delay, delay):
        cfg.logger.debug('Ping coroutine alive')
        ping_id = 1
        latency = random.randint(0, 50) + 50
        data = int.to_bytes(ping_id, 4, 'little') + int.to_bytes(latency, 4, 'little')
        try:
            await asyncio.sleep(initial_delay)
        except asyncio.exceptions.CancelledError:
            cfg.logger.debug('Ping coroutine canceled before first packet was sent')
            return
        while not self.writer.is_closing():
            try:
                await self.out_queue.put(Packet(cfg.codes.client_headers.PING, data))
                cfg.logger.debug(f'Sending ping message #{ping_id}')
                await asyncio.sleep(delay)
            except asyncio.exceptions.CancelledError:
                cfg.logger.debug('Ping coroutine canceled')
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
                await self.out_queue.put(Packet(cfg.codes.client_headers.KEEP_ALIVE, b''))
                await asyncio.sleep(delay)
            except asyncio.exceptions.CancelledError:
                cfg.logger.debug('Keep alive coroutine canceled')
                break

    async def roster_update_coroutine(self, initial_delay, delay):
        cfg.logger.debug('Roster update coroutine alive')
        try:
            await asyncio.sleep(initial_delay)
        except asyncio.exceptions.CancelledError:
            cfg.logger.debug('Roster update coroutine canceled before first packet was sent')
            return
        while not self.writer.is_closing():
            try:
                self.handler.update_roster()
                await asyncio.sleep(delay)
            except asyncio.exceptions.CancelledError:
                cfg.logger.debug('Roster update coroutine canceled')
                break
