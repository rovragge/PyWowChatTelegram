import asyncio

import PyByteBuffer

from src.common.config import cfg
from src.common.packet import Packet
from src.connector.base import Connector
from src.decoder.realm import RealmPacketDecoder
from src.handler.realm import RealmPacketHandler
from src.encoder.realm import RealmPacketEncoder


class RealmConnector(Connector):
    def __init__(self):
        super().__init__()
        self.decoder = RealmPacketDecoder()
        self.encoder = RealmPacketEncoder()
        self.handler = RealmPacketHandler(self.out_queue)

        self.srp_handler = None

    async def run(self):
        host, port = cfg.parse_realm_list()
        cfg.logger.info(f'Connecting to realm server: {host}:{port}')
        self.reader, self.writer = await asyncio.open_connection(host, port)
        self.receiver_task = asyncio.create_task(self.receiver(), name='receiver')
        self.sender_task = asyncio.create_task(self.sender(), name='sender')
        await self.out_queue.put(self.get_initial_packet())
        await asyncio.gather(self.receiver_task, self.sender_task)

    async def receiver(self):
        self.handler.handle_packet(await self.receive(119))  # logon challenge
        self.handler.handle_packet(await self.receive(32))  # logon proof
        self.handler.handle_packet(await self.receive(4096))  # realms
        self.writer.close()
        self.sender_task.cancel('received last message from realm server')

    def get_initial_packet(self):
        version = [bytes(x, 'utf-8') for x in cfg.version.split('.')]
        account = bytes(cfg.account, 'utf-8')
        buffer = PyByteBuffer.ByteBuffer.allocate(100)
        buffer.put(3 if cfg.expansion == 'Vanilla' else 8)
        buffer.put(30 + len(account), endianness='little', size=2)
        buffer.put(b'WoW\x00')
        buffer.put(version[0])
        buffer.put(version[1])
        buffer.put(version[2])
        buffer.put(cfg.build, endianness='little')
        buffer.put(self.str_to_int('x86'), endianness='little', size=4)
        buffer.put(self.str_to_int(cfg.platform), endianness='little', size=4)
        buffer.put(self.str_to_int(cfg.locale), endianness='little', size=4)
        buffer.put(b'\x00\x00\x00\x00\x7f\x00\x00\x01')  # 0 + 0 + 127 (size=4) + 0 + 0 + 1
        buffer.put(len(account))
        buffer.put(account)
        buffer.strip()
        buffer.rewind()
        return Packet(cfg.realm_packets.CMD_AUTH_LOGON_CHALLENGE, buffer.array())

    @staticmethod
    def str_to_int(string):
        return int.from_bytes(bytes(string, 'utf-8'), 'big')
