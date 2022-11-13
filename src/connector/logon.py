import PyByteBuffer

from src.common.config import glob
from src.connector.base import WoWConnector
from src.common.commonclasses import Packet
from src.handlers.logon import LogonPacketHandler


class LogonConnector(WoWConnector):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.srp_handler = None
        self.logon_done = False

    def get_handler(self):
        return LogonPacketHandler(self.out_queue)

    def get_initial_packet(self):
        version = [bytes(x, 'utf-8') for x in glob.logon_info.version.split('.')]
        account = bytes(glob.logon_info.account, 'utf-8')
        buffer = PyByteBuffer.ByteBuffer.allocate(100)
        buffer.put(3 if glob.logon_info.expansion == 'Vanilla' else 8)
        buffer.put(30 + len(account), endianness='little', size=2)
        buffer.put(b'WoW\x00')
        buffer.put(version[0])
        buffer.put(version[1])
        buffer.put(version[2])
        buffer.put(glob.logon_info.build, endianness='little')
        buffer.put(self.str_to_int('x86'), endianness='little', size=4)
        buffer.put(self.str_to_int(glob.logon_info.platform), endianness='little', size=4)
        buffer.put(self.str_to_int(glob.logon_info.locale), endianness='little', size=4)
        buffer.put(b'\x00\x00\x00\x00\x7f\x00\x00\x01')  # 0 + 0 + 127 (size=4) + 0 + 0 + 1
        buffer.put(len(account))
        buffer.put(account)
        buffer.strip()
        buffer.rewind()
        return Packet(glob.codes.server_headers.AUTH_LOGON_CHALLENGE, buffer.array())

    @staticmethod
    def str_to_int(string):
        return int.from_bytes(bytes(string, 'utf-8'), 'big')
