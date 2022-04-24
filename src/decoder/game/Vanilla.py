import PyByteBuffer

from src.common.config import cfg
from src.common.packet import Packet


class GamePacketDecoder:
    HEADER_LENGTH = 4

    def decode(self, data):
        buff = PyByteBuffer.ByteBuffer.wrap(data)
        size = 0
        packet_id = 0
        if buff.remaining < GamePacketDecoder.HEADER_LENGTH:
            cfg.logger.error(f'Game packet is less then {GamePacketDecoder.HEADER_LENGTH} bytes!')
            return
        if not size and not packet_id:
            packet_id, size = self.parse_game_header_encrypted(
                buff) if cfg.crypt.initialized else self.parse_game_header(buff)
        if size > buff.remaining:
            cfg.logger.error(f'Header size =  {size} while only {buff.remaining} bytes remaining')
            return
        packet_id, packet_data = self.decompress(packet_id, int.to_bytes(buff.get(size), size, 'big'))
        packet = Packet(packet_id, packet_data)
        cfg.logger.debug(f'RECV PACKET {packet}')
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
