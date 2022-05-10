from src.common.config import cfg
from src.encoder import Vanilla


class GamePacketEncoder(Vanilla.GamePacketEncoder):
    @staticmethod
    def is_unencrypted_packet(packet_id):
        return super().is_unencrypted_packet(packet_id) or packet_id == cfg.codes.WOW_CONNECTION
