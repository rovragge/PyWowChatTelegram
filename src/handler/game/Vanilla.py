from src.common.config import cfg
from src.common.packet import Packet


class GamePacketHandler:
    ADDON_INFO = b'V\x01\x00\x00x\x9cu\xcc\xbd\x0e\xc20\x0c\x04\xe0\xf2\x1e\xbc\x0ca@\x95\xc8B\xc3\x8cL\xe2"\x0b\xc7\xa9\x8c\xcbO\x9f\x1e\x16$\x06s\xebww\x81iY@\xcbi3g\xa3&\xc7\xbe[\xd5\xc7z\xdf}\x12\xbe\x16\xc0\x8cq$\xe4\x12I\xa8\xc2\xe4\x95H\n\xc9\xc5=\xd8\xb6z\x06K\xf84\x0f\x15Fsg\xbb8\xccz\xc7\x97\x8b\xbd\xdc&\xcc\xfe0B\xd6\xe6\xca\x01\xa8\xb8\x90\x80Q\xfc\xb7\xa4Pp\xb8\x12\xf3?&A\xfd\xb57\x90\x19f\x8f'

    def __init__(self, out_queue):
        self.out_queue = out_queue

    def handle_packet(self, packet):
        match packet.id:
            case cfg.game_packets.SMSG_AUTH_CHALLENGE:
                self.handle_SMSG_AUTH_CHALLENGE(packet)
            case cfg.game_packets.SMSG_AUTH_RESPONSE:
                self.handle_SMSG_AUTH_RESPONSE(packet)
            case cfg.game_packets.SMSG_NAME_QUERY:
                self.handle_SMSG_NAME_QUERY(packet)
            case cfg.game_packets.SMSG_CHAR_ENUM:
                self.handle_SMSG_CHAR_ENUM(packet)
            case cfg.game_packets.SMSG_LOGIN_VERIFY_WORLD:
                self.handle_SMSG_LOGIN_VERIFY_WORLD(packet)
            case cfg.game_packets.SMSG_GUILD_QUERY:
                self.handle_SMSG_GUILD_QUERY(packet)
            case cfg.game_packets.SMSG_GUILD_EVENT:
                self.handle_SMSG_GUILD_EVENT(packet)
            case cfg.game_packets.SMSG_GUILD_ROSTER:
                self.handle_SMSG_GUILD_ROSTER(packet)
            case cfg.game_packets.SMSG_MESSAGECHAT:
                self.handle_SMSG_MESSAGECHAT(packet)
            case cfg.game_packets.SMSG_CHANNEL_NOTIFY:
                self.handle_SMSG_CHANNEL_NOTIFY(packet)
            case cfg.game_packets.SMSG_NOTIFICATION:
                self.handle_SMSG_NOTIFICATION(packet)
            case cfg.game_packets.SMSG_WHO:
                self.handle_SMSG_WHO(packet)
            case cfg.game_packets.SMSG_SERVER_MESSAGE:
                self.handle_SMSG_SERVER_MESSAGE(packet)
            case cfg.game_packets.SMSG_INVALIDATE_PLAYER:
                self.handle_SMSG_INVALIDATE_PLAYER(packet)
            case cfg.game_packets.SMSG_WARDEN_DATA:
                self.handle_SMSG_WARDEN_DATA(packet)
            case cfg.game_packets.SMSG_GROUP_INVITE:
                self.handle_SMSG_GROUP_INVITE(packet)

    def handle_SMSG_AUTH_CHALLENGE(self, packet):
        challenge = self.parse_auth_challenge(packet)
        cfg.crypt.initialize(cfg.realm['session_key'])
        self.out_queue.put_nowait(Packet(cfg.game_packets.CMSG_AUTH_CHALLENGE, challenge))

    def parse_auth_challenge(self, packet):
        return

    def handle_SMSG_AUTH_RESPONSE(self, packet):
        pass

    def handle_SMSG_NAME_QUERY(self, packet):
        pass

    def handle_SMSG_CHAR_ENUM(self, packet):
        pass

    def handle_SMSG_LOGIN_VERIFY_WORLD(self, packet):
        pass

    def handle_SMSG_GUILD_QUERY(self, packet):
        pass

    def handle_SMSG_GUILD_EVENT(self, packet):
        pass

    def handle_SMSG_GUILD_ROSTER(self, packet):
        pass

    def handle_SMSG_MESSAGECHAT(self, packet):
        pass

    def handle_SMSG_CHANNEL_NOTIFY(self, packet):
        pass

    def handle_SMSG_NOTIFICATION(self, packet):
        pass

    def handle_SMSG_WHO(self, packet):
        pass

    def handle_SMSG_SERVER_MESSAGE(self, packet):
        pass

    def handle_SMSG_INVALIDATE_PLAYER(self, packet):
        pass

    def handle_SMSG_WARDEN_DATA(self, packet):
        pass

    def handle_SMSG_GROUP_INVITE(self, packet):
        pass
