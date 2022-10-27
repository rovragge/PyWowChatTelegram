import asyncio
import socket

import PyByteBuffer

from src.common.config import glob
from src.connector.base import WoWConnector
from src.common.commonclasses import Packet
from src.handlers.logon import LogonPacketHandler


class LogonConnector(WoWConnector):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.srp_handler = None
        self.logon_finished = False

    def get_handler(self):
        return LogonPacketHandler(self.out_queue)

    async def run(self):
        await self.out_queue.put(self.get_initial_packet())
        glob.logger.info(f'Connecting to logon server: {glob.connection_info.host}')
        try:
            self.reader, self.writer = await asyncio.open_connection(glob.connection_info.host,
                                                                     glob.connection_info.port)
        except socket.gaierror:
            glob.logger.error('Can\'t establish connection')
            return
        self.main_task = asyncio.gather(self.receiver_coro(), self.sender_coro(), self.handler_coro())
        try:
            await self.main_task
        except asyncio.exceptions.CancelledError:
            return

    def handle_result(self, result):
        match result:
            case 1:
                self.writer.close()
                self.main_task.cancel()

    def get_initial_packet(self):
        version = [bytes(x, 'utf-8') for x in glob.connection_info.version.split('.')]
        account = bytes(glob.connection_info.account, 'utf-8')
        buffer = PyByteBuffer.ByteBuffer.allocate(100)
        buffer.put(3 if glob.connection_info.expansion == 'Vanilla' else 8)
        buffer.put(30 + len(account), endianness='little', size=2)
        buffer.put(b'WoW\x00')
        buffer.put(version[0])
        buffer.put(version[1])
        buffer.put(version[2])
        buffer.put(glob.connection_info.build, endianness='little')
        buffer.put(self.str_to_int('x86'), endianness='little', size=4)
        buffer.put(self.str_to_int(glob.connection_info.platform), endianness='little', size=4)
        buffer.put(self.str_to_int(glob.connection_info.locale), endianness='little', size=4)
        buffer.put(b'\x00\x00\x00\x00\x7f\x00\x00\x01')  # 0 + 0 + 127 (size=4) + 0 + 0 + 1
        buffer.put(len(account))
        buffer.put(account)
        buffer.strip()
        buffer.rewind()
        return Packet(glob.codes.server_headers.AUTH_LOGON_CHALLENGE, buffer.array())

    @staticmethod
    def str_to_int(string):
        return int.from_bytes(bytes(string, 'utf-8'), 'big')
