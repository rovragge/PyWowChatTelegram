from src.common.config import cfg
from src.handler.game import Vanilla


class GamePacketHandler(Vanilla.GamePacketHandler):
    ADDON_INFO = b'\xd0\x01\x00\x00x\x9cu\xcf;\x0e\xc20\x0c\x80\xe1r\x0f.C\x18P\xa5f\xa1eF&q+\xab\x89S\x19\x87GO\x0f\x0bbq\xbd~\xd6o\xd9%ZW\x90x=\xd4\xa0T\xf8\xd26\xbb\xfc\xdcw\xcdw\xdc\xcf\x1c\xa8&\x1c\tS\xf4\xc4\x94a\xb1\x96\x88#\xf1d\x06\x8e%\xdf@\xbb2m\xda\x80/\xb5P`T3y\xf2}\x95\x07\xbem\xac\x94\xa2\x03\x9eMm\xf9\xbe`\xb0\xb3\xadb\xeeK\x98Q\xb7~\xf1\x10\xa4\x98r\x06\x8a&\x0c\x90\x90\xed{\x83@\xc4~\xa6\x94\xb6\x98\x18\xc56\xca\xe8\x81aB\xf9\xeb\x07c\xab\x8b\xec'

    def handle_packet(self, packet):
        match packet.id:
            case cfg.game_packets.SMSG_GM_MESSAGECHAT:
                self.handle_SMSG_GM_MESSAGECHAT(packet)
            case cfg.game_packets.SMSG_MOTD:
                self.handle_SMSG_MOTD(packet)
            case cfg.game_packets.SMSG_TIME_SYNC_REQ:
                self.handle_SMSG_TIME_SYNC_REQ(packet)
            case _:
                super().handle_packet(packet)

    def handle_SMSG_GM_MESSAGECHAT(self, packet):
        pass

    def handle_SMSG_MOTD(self, packet):
        pass

    def handle_SMSG_TIME_SYNC_REQ(self, packet):
        pass

