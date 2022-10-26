import src.codes.Vanilla as Vanilla


class ServerHeaders(Vanilla.ServerHeaders):
    GM_MESSAGECHAT = 0x03B2
    MOTD = 0x033D


class ClientHeaders(Vanilla.ClientHeaders):
    KEEP_ALIVE = 0x0406


class ChatChannels(Vanilla.ChatChannels):
    SYSTEM = 0x00
    SAY = 0x01
    GUILD = 0x04
    OFFICER = 0x05
    YELL = 0x06
    WHISPER = 0x07
    TEXT_EMOTE = 0x0B
    CHANNEL = 0x11
    CHANNEL_JOIN = 0x12
    CHANNEL_LEAVE = 0x13
    CHANNEL_LIST = 0x14
    CHANNEL_NOTICE = 0x15
    CHANNEL_NOTICE_USER = 0x16
    GUILD_RECRUITMENT = 0x19
    EMOTE = 0x0A
    ANNOUNCEMENT = 0xFF

class Codes(Vanilla.Codes):
    client_headers = ClientHeaders
    server_headers = ServerHeaders
    chat_channels = ChatChannels
