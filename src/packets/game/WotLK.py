from src.packets.game import TBC


class GamePackets(TBC.GamePackets):
    # General messages
    SMSG_GM_MESSAGECHAT = 0x03B3
    CMSG_KEEP_ALIVE = 0x0407
