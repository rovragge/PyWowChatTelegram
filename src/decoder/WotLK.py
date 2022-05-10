from src.common.config import cfg
from src.decoder import Vanilla


class PacketDecoder(Vanilla.PacketDecoder):
    def parse_encrypted_header(self, buff):
        header = int.to_bytes(buff.get(PacketDecoder.HEADER_LENGTH), PacketDecoder.HEADER_LENGTH, 'big')
        decrypted = cfg.crypt.decrypt(header)

        if decrypted[0] & 128 == 128:
            next_byte = cfg.crypt.decrypt(int.to_bytes(buff.get(1), 1, 'big'))[0]
            size = (((decrypted[0] & 127) << 16) | ((decrypted[1] & 255) << 8) | (decrypted[2] & 255)) - 2
            packet_id = (next_byte & 255) << 8 | decrypted[3] & 255
        else:
            size = ((decrypted[0] & 255) << 8 | decrypted[1] & 255) - 2
            packet_id = (decrypted[3] & 255) << 8 | decrypted[2] & 255
        return packet_id, size
