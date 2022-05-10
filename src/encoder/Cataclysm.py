from src.common.config import cfg
from src.encoder import Vanilla


class PacketEncoder(Vanilla.PacketEncoder):
    @staticmethod
    def is_unencrypted_packet(packet_id):
        return super().is_unencrypted_packet(packet_id) or packet_id == cfg.codes.WOW_CONNECTION
