from src.common.config import cfg
from src.encoder.game import Vanilla


class GamePacketEncoder(Vanilla.GamePacketEncoder):
    @staticmethod
    def is_unencrypted_packet(packet_id):
        return super().is_unencrypted_packet(packet_id) or packet_id == cfg.game_packets.WOW_CONNECTION
