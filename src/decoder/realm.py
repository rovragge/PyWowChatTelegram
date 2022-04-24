import PyByteBuffer

from src.common.config import cfg
from src.common.packet import Packet


class RealmPacketDecoder:
    def decode(self, data):
        size = 0
        in_buff = PyByteBuffer.ByteBuffer.wrap(data)
        if not in_buff.remaining:
            cfg.logger.error('Received packet has no data')
            return
        packet_id = in_buff.get(1)
        match packet_id:
            case cfg.realm_packets.CMD_AUTH_LOGON_CHALLENGE:
                if in_buff.remaining < 2:
                    cfg.logger.error(
                        f'Packet recognized as CMD_AUTH_LOGON_CHALLENGE, but no data ({in_buff.remaining} bytes)')
                    return
                saved_position = in_buff.position
                in_buff.get(1)
                size = 118 if cfg.realm_packets.AUTH.is_success(in_buff.get(1)) else 2
                self.reset_position(saved_position, in_buff)
            case cfg.realm_packets.CMD_AUTH_LOGON_PROOF:
                if in_buff.remaining < 1:
                    cfg.logger.error(
                        f'Packet recognized as CMD_AUTH_LOGON_PROOF, but no data ({in_buff.remaining} bytes)')
                    return
                saved_position = in_buff.position
                if cfg.realm_packets.AUTH.is_success(in_buff.get(1)):
                    size = 25 if cfg.expansion == 'Vanilla' else 31
                else:
                    size = 1 if not in_buff.remaining else 3
                self.reset_position(saved_position, in_buff)
            case cfg.realm_packets.CMD_REALM_LIST:
                if in_buff.remaining < 2:
                    cfg.logger.error(f'Packet recognized as CMD_REALM_LIST, but no data ({in_buff.remaining} bytes)')
                    return
                size = in_buff.get(2, endianness='little')
        if size > in_buff.remaining:
            cfg.logger.error(f'Calculated buffer size = {size} while only {in_buff.remaining} bytes remaining')
            return
        packet = Packet(packet_id, in_buff.slice().array(size))
        cfg.logger.debug(f'RECV REALM PACKET: {packet}')
        return packet

    @staticmethod
    def reset_position(saved_position, buff):
        buff.remaining += buff.position - saved_position
        buff.position = saved_position
