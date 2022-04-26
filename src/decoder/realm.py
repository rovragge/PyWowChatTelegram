import PyByteBuffer

from src.common.config import cfg
from src.common.packet import Packet


class RealmPacketDecoder:
    def __init__(self):
        self.size = None
        self.packet_id = None
        self.remaining_data = None
        self.incomplete_packet = False

    def decode(self, buff):
        if not self.packet_id:
            self.packet_id = buff.get(1)
        if not self.size:
            match self.packet_id:
                case cfg.realm_packets.CMD_AUTH_LOGON_CHALLENGE:
                    if buff.remaining < 2:
                        self.incomplete_packet = True
                        self.remaining_data = buff.array()
                        return
                    saved_position = buff.position
                    buff.get(1)
                    self.size = 118 if cfg.auth_results.is_success(buff.get(1)) else 2
                    self.reset_position(saved_position, buff)
                case cfg.realm_packets.CMD_AUTH_LOGON_PROOF:
                    if buff.remaining < 1:
                        self.incomplete_packet = True
                        self.remaining_data = buff.array()
                        return
                    saved_position = buff.position
                    if cfg.auth_results.is_success(buff.get(1)):
                        self.size = 25 if cfg.expansion == 'Vanilla' else 31
                    else:
                        self.size = 1 if not buff.remaining else 3
                    self.reset_position(saved_position, buff)
                case cfg.realm_packets.CMD_REALM_LIST:
                    if buff.remaining < 2:
                        self.incomplete_packet = True
                        self.remaining_data = buff.array()
                        return None
                    self.size = buff.get(2, endianness='little')
        if self.size > buff.remaining:
            self.incomplete_packet = True
            self.remaining_data = buff.array()
            return
        packet = Packet(self.packet_id, buff.array(self.size))
            self.incomplete_packet = bool(buff.remaining)
        self.remaining_data = None
        self.size = None
        self.packet_id = None
        return packet

    @staticmethod
    def reset_position(saved_position, buff):
        buff.remaining += buff.position - saved_position
        buff.position = saved_position
