from src.encoder.game import Cataclysm


class GamePacketEncoder(Cataclysm.GamePacketEncoder):
    def encode(self, packet):
        header_size = 4
        size = len(packet.data)
        pass  # TBD
