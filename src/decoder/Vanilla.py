from src.common.config import cfg
from src.common.dataclasses import Packet


class PacketDecoder:
    HEADER_LENGTH = 4

    def __init__(self):
        self.packet_size = None
        self.packet_id = None
        self.remaining_data = None
        self.incomplete_packet = False

    def decode(self, buff, is_game):
        if not is_game:
            return self.decode_logon(buff)
        if not self.packet_size and not self.packet_id:
            if buff.remaining < PacketDecoder.HEADER_LENGTH:
                self.incomplete_packet = True
                self.remaining_data = buff.array()
                return
            self.packet_id, self.packet_size = self.parse_encrypted_header(
                buff) if cfg.crypt.initialized else self.parse_header(buff)
        return self.compose_packet(buff)

    def decode_logon(self, buff):
        if not self.packet_id:
            self.packet_id = buff.get(1)
        if not self.packet_size:
            match self.packet_id:
                case cfg.codes.realm_headers.AUTH_LOGON_CHALLENGE:
                    if buff.remaining < 2:
                        self.incomplete_packet = True
                        self.remaining_data = buff.array()
                        return
                    saved_position = buff.position
                    buff.get(1)
                    self.packet_size = 118 if cfg.codes.logon_auth_results.is_success(buff.get(1)) else 2
                    self.reset_position(saved_position, buff)
                case cfg.codes.realm_headers.AUTH_LOGON_PROOF:
                    if buff.remaining < 1:
                        self.incomplete_packet = True
                        self.remaining_data = buff.array()
                        return
                    saved_position = buff.position
                    if cfg.codes.logon_auth_results.is_success(buff.get(1)):
                        self.packet_size = 25 if cfg.expansion == 'Vanilla' else 31
                    else:
                        self.packet_size = 1 if not buff.remaining else 3
                    self.reset_position(saved_position, buff)
                case cfg.codes.realm_headers.REALM_LIST:
                    if buff.remaining < 2:
                        self.incomplete_packet = True
                        self.remaining_data = buff.array()
                        return None
                    self.packet_size = buff.get(2, endianness='little')
        return self.compose_packet(buff)

    def compose_packet(self, buff):
        if self.packet_size > buff.remaining:
            self.incomplete_packet = True
            self.remaining_data = buff.array()
            return
        packet = Packet(
            *self.decompress(self.packet_id, buff.array(self.packet_size) if self.packet_size else bytearray(1)))
        self.incomplete_packet = bool(buff.remaining)
        self.remaining_data = None
        self.packet_size = None
        self.packet_id = None
        return packet

    def parse_encrypted_header(self, buff):
        header = buff.get(PacketDecoder.HEADER_LENGTH)
        decrypted = cfg.crypt.decrypt(header)
        size = ((decrypted[0] & 0xFF) << 8 | decrypted[1] & 0xFF) - 2
        packet_id = (decrypted[3] & 0xFF) << 8 | decrypted[2] & 0xFF
        return size, packet_id

    def decompress(self, packet_id, data):
        return packet_id, data  # added in cata

    @staticmethod
    def parse_header(buff):
        size = buff.get(2) - 2
        packet_id = buff.get(2, 'little')
        return packet_id, size

    @staticmethod
    def reset_position(saved_position, buff):
        buff.remaining += buff.position - saved_position
        buff.position = saved_position
