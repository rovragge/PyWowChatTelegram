from src.encoder import Cataclysm


class PacketEncoder(Cataclysm.PacketEncoder):
    def encode(self, packet):
        header_size = 4
        size = len(packet.data)
        pass  # TBD
