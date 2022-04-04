import logging
import packets.game


class GameConnector:
    def __init__(self, cfg, reader, writer):
        self.cfg = cfg
        self.reader = reader
        self.writer = writer
        self.packets = packets.game.get(self.cfg.get_expansion())

    async def connect(self, realm):
        logging.info(f'Connecting to realm {realm["name"]} ({realm["host"]}:{realm["port"]})')
