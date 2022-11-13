from src.common.config import glob
from src.common.commonclasses import Packet
from src.common.WowData import WowData


class PacketDecoder:
    HEADER_LENGTH = 4

    def __init__(self):
        self.packet_size = None
        self.packet_id = None
        self.remaining_data = None
        self.incomplete_packet = False

    def decode(self, buff, logon_done):
        if not logon_done:
            return self.decode_logon(buff)
        if not self.packet_size and not self.packet_id:
            if buff.remaining < PacketDecoder.HEADER_LENGTH:
                self.incomplete_packet = True
                self.remaining_data = buff.array()
                return
            self.packet_id, self.packet_size = self.parse_encrypted_header(
                buff) if glob.crypt.initialized else self.parse_header(buff)
        return self.compose_packet(buff)

    def decode_logon(self, buff):
        if not self.packet_id:
            self.packet_id = buff.get(1)
        if not self.packet_size:
            match self.packet_id:
                case glob.codes.server_headers.AUTH_LOGON_CHALLENGE:
                    self.packet_size = self.get_challenge_size(buff)
                case glob.codes.server_headers.AUTH_LOGON_PROOF:
                    self.packet_size = self.get_proof_size(buff)
                case glob.codes.server_headers.REALM_LIST:
                    self.packet_size = self.get_realm_list_size(buff)
                case _:
                    glob.logger.critical('Unknown logon header')
                    raise ValueError
        return None if not self.packet_size else self.compose_packet(buff)

    def get_challenge_size(self, buff):
        if buff.remaining < 2:
            self.incomplete_packet = True
            self.remaining_data = buff.array()
            return
        saved_position = buff.position
        buff.get(1)
        packet_size = 118 if glob.codes.logon_auth_results.is_success(buff.get(1)) else 2
        self.reset_position(saved_position, buff)
        return packet_size

    def get_proof_size(self, buff):
        if buff.remaining < 1:
            self.incomplete_packet = True
            self.remaining_data = buff.array()
            return
        saved_position = buff.position
        self.reset_position(saved_position, buff)
        if glob.codes.logon_auth_results.is_success(buff.get(1)):
            return 31
        else:
            return 1 if not buff.remaining else 3

    def get_realm_list_size(self, buff):
        if buff.remaining < 2:
            self.incomplete_packet = True
            self.remaining_data = buff.array()
            return
        return buff.get(2, endianness='little')

    def compose_packet(self, buff):
        if self.packet_size > buff.remaining:
            self.incomplete_packet = True
            self.remaining_data = buff.array()
            return
        packet = Packet(self.packet_id,
                        WowData(buff.array(self.packet_size)) if self.packet_size else WowData(bytearray(1)))
        self.incomplete_packet = bool(buff.remaining)
        self.remaining_data = None
        self.packet_size = None
        self.packet_id = None
        return packet

    @staticmethod
    def parse_encrypted_header(buff):
        header = int.to_bytes(buff.get(PacketDecoder.HEADER_LENGTH), PacketDecoder.HEADER_LENGTH, 'big')
        decrypted = glob.crypt.decrypt(header)

        if decrypted[0] & 128 == 128:
            next_byte = glob.crypt.decrypt(int.to_bytes(buff.get(1), 1, 'big'))[0]
            size = (((decrypted[0] & 127) << 16) | ((decrypted[1] & 255) << 8) | (decrypted[2] & 255)) - 2
            packet_id = (next_byte & 255) << 8 | decrypted[3] & 255
        else:
            size = ((decrypted[0] & 255) << 8 | decrypted[1] & 255) - 2
            packet_id = (decrypted[3] & 255) << 8 | decrypted[2] & 255
        return packet_id, size

    @staticmethod
    def parse_header(buff):
        size = buff.get(2) - 2
        packet_id = buff.get(2, 'little')
        return packet_id, size

    @staticmethod
    def reset_position(saved_position, buff):
        buff.remaining += buff.position - saved_position
        buff.position = saved_position
