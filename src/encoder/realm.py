class RealmPacketEncoder:
    @staticmethod
    def encode(packet):
        size = 2 if packet.id > 255 else 1
        return int.to_bytes(packet.id, size, 'big') + packet.data
