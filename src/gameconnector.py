import asyncio
import logging

import connector
import packets.game


class GameConnector(connector.Connector):
    def __init__(self, cfg, realm):
        super().__init__(cfg)
        self.realm = realm
        self.packets = packets.game.get(self.cfg.get_expansion())

    async def connect(self):
        logging.info(f'Connecting to realm: {self.realm["name"]}')
        self.reader, self.writer = await asyncio.open_connection(self.realm["host"], self.realm["port"])
        data = await self.reader.read(64)
        packet = self.handle_game_packet(self.decode(data))
        # await self.send(packet)
        self.writer.close()

    def decode(self, data):
        packet = connector.Packet(None, None)
        return packet

    def handle_game_packet(self, packet):
        match packet:
            case _:
                return 1
