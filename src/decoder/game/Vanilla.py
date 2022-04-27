from src.common.config import cfg
from src.common.packet import Packet


class GamePacketDecoder:
    HEADER_LENGTH = 4

    def __init__(self):
        self.size = None
        self.packet_id = None
        self.remaining_data = None
        self.incomplete_packet = False

    def decode(self, buff):
        if not self.size and not self.packet_id:
            if buff.remaining < GamePacketDecoder.HEADER_LENGTH:
                self.incomplete_packet = True
                self.remaining_data = buff.array()
                return
            self.packet_id, self.size = self.parse_game_header_encrypted(
                buff) if cfg.crypt.initialized else self.parse_game_header(buff)
        if self.size > buff.remaining:
            self.incomplete_packet = True
            self.remaining_data = buff.array()
            return
        packet = Packet(*self.decompress(self.packet_id, buff.array(self.size)))
        self.incomplete_packet = bool(buff.remaining)
        self.remaining_data = None
        self.size = None
        self.packet_id = None
        return packet

    def parse_game_header(self, buff):
        size = buff.get(2) - 2
        packet_id = buff.get(2, 'little')
        return packet_id, size

    def parse_game_header_encrypted(self, buff):
        header = buff.get(GamePacketDecoder.HEADER_LENGTH)
        decrypted = cfg.crypt.decrypt(header)
        size = ((decrypted[0] & 0xFF) << 8 | decrypted[1] & 0xFF) - 2
        packet_id = (decrypted[3] & 0xFF) << 8 | decrypted[2] & 0xFF
        return size, packet_id

    def decompress(self, packet_id, data):
        return packet_id, data
