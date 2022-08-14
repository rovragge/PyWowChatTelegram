from src.common.config import glob


class PacketEncoder:
    def encode(self, packet, is_game):
        if not is_game:
            size = 2 if packet.id > 255 else 1
            return int.to_bytes(packet.id, size, 'big') + packet.data
        unencrypted = self.is_unencrypted_packet(packet.id)
        header_size = 4 if unencrypted else 6
        btarr = bytearray()
        btarr += int.to_bytes(len(packet.data) + header_size - 2, 2, 'big')
        btarr += int.to_bytes(packet.id, 2, 'little')
        header = btarr if unencrypted else glob.crypt.encrypt(btarr + bytearray(2))
        return header + packet.data

    @staticmethod
    def is_unencrypted_packet(packet_id):
        return packet_id == glob.codes.client_headers.AUTH_CHALLENGE
