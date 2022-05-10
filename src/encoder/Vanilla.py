from src.common.config import cfg


class GamePacketEncoder:
    def encode(self, packet):
        unencrypted = self.is_unencrypted_packet(packet.id)
        header_size = 4 if unencrypted else 6
        btarr = bytearray()
        btarr += int.to_bytes(len(packet.data) + header_size - 2, 2, 'big')
        btarr += int.to_bytes(packet.id, 2, 'little')
        header = btarr if unencrypted else cfg.crypt.encrypt(btarr + bytearray(2))
        return header + packet.data

    @staticmethod
    def is_unencrypted_packet(packet_id):
        return packet_id == cfg.codes.client_headers.AUTH_CHALLENGE
