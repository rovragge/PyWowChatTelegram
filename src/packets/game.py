import logging


class Vanilla:
    # General messages
    CMSG_CHAR_ENUM = 0x37
    SMSG_CHAR_ENUM = 0x3B
    CMSG_PLAYER_LOGIN = 0x3D
    CMSG_LOGOUT_REQUEST = 0x4B
    CMSG_NAME_QUERY = 0x50
    SMSG_NAME_QUERY = 0x51
    CMSG_GUILD_QUERY = 0x54
    SMSG_GUILD_QUERY = 0x55
    CMSG_WHO = 0x62
    SMSG_WHO = 0x63
    CMSG_GUILD_ROSTER = 0x89
    SMSG_GUILD_ROSTER = 0x8A
    SMSG_GUILD_EVENT = 0x92
    CMSG_MESSAGECHAT = 0x95
    SMSG_MESSAGECHAT = 0x96
    CMSG_JOIN_CHANNEL = 0x97
    SMSG_CHANNEL_NOTIFY = 0x99
    SMSG_NOTIFICATION = 0x01CB
    CMSG_PING = 0x01DC
    SMSG_AUTH_CHALLENGE = 0x01EC
    CMSG_AUTH_CHALLENGE = 0x01ED
    SMSG_AUTH_RESPONSE = 0x01EE
    SMSG_LOGIN_VERIFY_WORLD = 0x0236
    SMSG_SERVER_MESSAGE = 0x0291
    SMSG_WARDEN_DATA = 0x02E6
    CMSG_WARDEN_DATA = 0x02E7
    SMSG_INVALIDATE_PLAYER = 0x031C
    SMSG_GROUP_INVITE = 0x06F
    CMSG_GROUP_INVITE = 0x06E
    SMSG_TIME_SYNC_REQ = 0x0390
    CMSG_TIME_SYNC_RESP = 0x039
    # Guild events
    GE_PROMOTED = 0x00
    GE_DEMOTED = 0x01
    GE_MOTD = 0x02
    GE_JOINED = 0x03
    GE_LEFT = 0x04
    GE_REMOVED = 0x05
    GE_SIGNED_ON = 0x0C
    GE_SIGNED_OFF = 0x0D

    # Chat messages
    CHAT_MSG_SAY = 0x00
    CHAT_MSG_GUILD = 0x03
    CHAT_MSG_OFFICER = 0x04
    CHAT_MSG_YELL = 0x05
    CHAT_MSG_WHISPER = 0x06
    CHAT_MSG_EMOTE = 0x08
    CHAT_MSG_TEXT_EMOTE = 0x09
    CHAT_MSG_CHANNEL = 0x0E
    CHAT_MSG_SYSTEM = 0x0A
    CHAT_MSG_CHANNEL_JOIN = 0x0F
    CHAT_MSG_CHANNEL_LEAVE = 0x10
    CHAT_MSG_CHANNEL_LIST = 0x11
    CHAT_MSG_CHANNEL_NOTICE = 0x12
    CHAT_MSG_CHANNEL_NOTICE_USER = 0x13
    CHAT_MSG_ACHIEVEMENT = 0x30
    CHAT_MSG_GUILD_ACHIEVEMENT = 0x31

    # Auth result
    AUTH_OK = 0x0C
    AUTH_FAILED = 0x0D
    AUTH_REJECT = 0x0E
    AUTH_BAD_SERVER_PROOF = 0x0F
    AUTH_UNAVAILABLE = 0x10
    AUTH_SYSTEM_ERROR = 0x11
    AUTH_BILLING_ERROR = 0x12
    AUTH_BILLING_EXPIRED = 0x13
    AUTH_VERSION_MISMATCH = 0x14
    AUTH_UNKNOWN_ACCOUNT = 0x15
    AUTH_INCORRECT_PASSWORD = 0x16
    AUTH_SESSION_EXPIRED = 0x17
    AUTH_SERVER_SHUTTING_DOWN = 0x18
    AUTH_ALREADY_LOGGING_IN = 0x19
    AUTH_LOGIN_SERVER_NOT_FOUND = 0x1A
    AUTH_WAIT_QUEUE = 0x1B
    AUTH_BANNED = 0x1C
    AUTH_ALREADY_ONLINE = 0x1D
    AUTH_NO_TIME = 0x1E
    AUTH_DB_BUSY = 0x1F
    AUTH_SUSPENDED = 0x20
    AUTH_PARENTAL_CONTROL = 0x21

    # Chat notifications
    CHAT_JOINED_NOTICE = 0x00
    CHAT_LEFT_NOTICE = 0x01
    CHAT_YOU_JOINED_NOTICE = 0x02
    CHAT_YOU_LEFT_NOTICE = 0x03
    CHAT_WRONG_PASSWORD_NOTICE = 0x04
    CHAT_NOT_MEMBER_NOTICE = 0x05
    CHAT_NOT_MODERATOR_NOTICE = 0x06
    CHAT_PASSWORD_CHANGED_NOTICE = 0x07
    CHAT_OWNER_CHANGED_NOTICE = 0x08
    CHAT_PLAYER_NOT_FOUND_NOTICE = 0x09
    CHAT_NOT_OWNER_NOTICE = 0x0A
    CHAT_CHANNEL_OWNER_NOTICE = 0x0B
    CHAT_MODE_CHANGE_NOTICE = 0x0C
    CHAT_ANNOUNCEMENTS_ON_NOTICE = 0x0D
    CHAT_ANNOUNCEMENTS_OFF_NOTICE = 0x0E
    CHAT_MODERATION_ON_NOTICE = 0x0F
    CHAT_MODERATION_OFF_NOTICE = 0x10
    CHAT_MUTED_NOTICE = 0x11
    CHAT_PLAYER_KICKED_NOTICE = 0x12
    CHAT_BANNED_NOTICE = 0x13
    CHAT_PLAYER_BANNED_NOTICE = 0x14
    CHAT_PLAYER_UNBANNED_NOTICE = 0x15
    CHAT_PLAYER_NOT_BANNED_NOTICE = 0x16
    CHAT_PLAYER_ALREADY_MEMBER_NOTICE = 0x17
    CHAT_INVITE_NOTICE = 0x18
    CHAT_INVITE_WRONG_FACTION_NOTICE = 0x19
    CHAT_WRONG_FACTION_NOTICE = 0x1A
    CHAT_INVALID_NAME_NOTICE = 0x1B
    CHAT_NOT_MODERATED_NOTICE = 0x1C
    CHAT_PLAYER_INVITED_NOTICE = 0x1D
    CHAT_PLAYER_INVITE_BANNED_NOTICE = 0x1E
    CHAT_THROTTLED_NOTICE = 0x1F
    CHAT_NOT_IN_AREA_NOTICE = 0x20
    CHAT_NOT_IN_LFG_NOTICE = 0x21
    CHAT_VOICE_ON_NOTICE = 0x22
    CHAT_VOICE_OFF_NOTICE = 0x23

    # Server messages
    SERVER_MSG_SHUTDOWN_TIME = 0x01
    SERVER_MSG_RESTART_TIME = 0x02
    SERVER_MSG_CUSTOM = 0x03
    SERVER_MSG_SHUTDOWN_CANCELLED = 0x04
    SERVER_MSG_RESTART_CANCELLED = 0x05

    # Races
    RACE_HUMAN = 0x01
    RACE_ORC = 0x02
    RACE_DWARF = 0x03
    RACE_NIGHTELF = 0x04
    RACE_UNDEAD = 0x05
    RACE_TAUREN = 0x06
    RACE_GNOME = 0x07
    RACE_TROLL = 0x08
    RACE_GOBLIN = 0x09
    RACE_BLOODELF = 0x0A
    RACE_DRAENEI = 0x0B
    RACE_WORGEN = 0x16
    RACE_PANDAREN_NEUTRAL = 0x18
    RACE_PANDAREN_ALLIANCE = 0x19
    RACE_PANDAREN_HORDE = 0x1A

    # Classes
    CLASS_WARRIOR = 0x01
    CLASS_PALADIN = 0x02
    CLASS_HUNTER = 0x03
    CLASS_ROGUE = 0x04
    CLASS_PRIEST = 0x05
    CLASS_DEATH_KNIGHT = 0x06
    CLASS_SHAMAN = 0x07
    CLASS_MAGE = 0x08
    CLASS_WARLOCK = 0x09
    CLASS_MONK = 0x0A
    CLASS_DRUID = 0x0B

    # Genders
    GENDER_MALE = 0
    GENDER_FEMALE = 1
    GENDER_NONE = 2

    # Chat channels
    CHANNEL_GENERAL = 0x01
    CHANNEL_TRADE = 0x02
    CHANNEL_LOCAL_DEFENSE = 0x16
    CHANNEL_WORLD_DEFENSE = 0x17
    CHANNEL_GUILD_RECRUITMENT = 0x00
    CHANNEL_LOOKING_FOR_GROUP = 0x1A

    @classmethod
    def get_language(cls, race):
        match race:
            case cls.RACE_ORC | cls.RACE_UNDEAD | cls.RACE_TAUREN | cls.RACE_TROLL \
                 | cls.RACE_BLOODELF | cls.RACE_GOBLIN | cls.RACE_PANDAREN_HORDE:
                return 0x01  # orcish
            case cls.RACE_PANDAREN_NEUTRAL:
                return 0x2A
            case _:
                return 0x07  # common

    @classmethod
    def get_race_str(cls, race):
        match race:
            case cls.RACE_HUMAN:
                return 'Human'
            case cls.RACE_ORC:
                return 'Orc'
            case cls.RACE_DWARF:
                return 'Dwarf'
            case cls.RACE_NIGHTELF:
                return 'Night Elf'
            case cls.RACE_UNDEAD:
                return 'Undead'
            case cls.RACE_TAUREN:
                return 'Tauren'
            case cls.RACE_GNOME:
                return 'Gnome'
            case cls.RACE_TROLL:
                return 'Troll'
            case cls.RACE_GOBLIN:
                return 'Goblin'
            case cls.RACE_BLOODELF:
                return 'Blood Elf'
            case cls.RACE_DRAENEI:
                return 'Draenei'
            case cls.RACE_WORGEN:
                return 'Worgen'
            case cls.RACE_PANDAREN_NEUTRAL:
                return 'Pandaren'
            case cls.RACE_PANDAREN_ALLIANCE:
                return 'Allince Pandaren'
            case cls.RACE_PANDAREN_HORDE:
                return 'Horde Pandaren'
            case _:
                logging.error(f'No string for this race: {race}')
                return 'Unknown race'

    @classmethod
    def get_gender_str(cls, gender):
        match gender:
            case cls.GENDER_MALE:
                return 'Male'
            case cls.GENDER_FEMALE:
                return 'Female'
            case _:
                logging.error(f'No string for this gender: {gender}')
                return 'Unknown gender'

    @classmethod
    def get_class_str(cls, char_class):
        match char_class:
            case cls.CLASS_WARRIOR:
                return 'Warrior'
            case cls.CLASS_PALADIN:
                return 'Paladin'
            case cls.CLASS_HUNTER:
                return 'Hunter'
            case cls.CLASS_ROGUE:
                return 'Rogue'
            case cls.CLASS_DEATH_KNIGHT:
                return 'Death Knight'
            case cls.CLASS_PRIEST:
                return 'Priest'
            case cls.CLASS_SHAMAN:
                return 'Shaman'
            case cls.CLASS_MAGE:
                return 'Mage'
            case cls.CLASS_WARLOCK:
                return 'Warlock'
            case cls.CLASS_MONK:
                return 'Monk'
            case cls.CLASS_DRUID:
                return 'Druid'
            case _:
                logging.error(f'No string for this class: {char_class}')
                return 'Unknown class'

    @classmethod
    def get_auth_message_str(cls, auth_result):
        match auth_result:
            case cls.AUTH_OK:
                return 'Success!'
            case cls.AUTH_UNKNOWN_ACCOUNT:
                return 'Incorrect username!'
            case cls.AUTH_INCORRECT_PASSWORD:
                return 'Incorrect password!'
            case cls.AUTH_VERSION_MISMATCH:
                return 'Invalid game version for this server'
            case cls.AUTH_BANNED:
                return 'Your account has been banned!'
            case cls.AUTH_ALREADY_LOGGING_IN | cls.AUTH_ALREADY_ONLINE:
                return 'Your account is already online! Log it off or wait a minute if already logging off'
            case cls.AUTH_SUSPENDED:
                return 'Your account has been suspended!'
            case _:
                return f'Failed to login to game server! authResult: {auth_result}'

    @classmethod
    def get_channel_str(cls, channel):
        match channel:
            case cls.CHAT_MSG_SAY:
                return 'Say'
            case cls.CHAT_MSG_GUILD:
                return 'Guild'
            case cls.CHAT_MSG_OFFICER:
                return 'Officer'
            case cls.CHAT_MSG_YELL:
                return 'Yell'
            case cls.CHAT_MSG_WHISPER:
                return 'Whisper'
            case cls.CHAT_MSG_EMOTE | cls.CHAT_MSG_TEXT_EMOTE:
                return 'Emote'
            case cls.CHAT_MSG_CHANNEL:
                return 'Channel'
            case cls.CHAT_MSG_SYSTEM:
                return 'System'
            case _:
                logging.error(f'No string for this chat channel: {channel}')
                return 'Unknown channel'

    @classmethod
    def get_channel(cls, channel_str):
        match channel_str.lower():
            case 'system':
                return cls.CHAT_MSG_SYSTEM
            case 'say':
                return cls.CHAT_MSG_SAY
            case 'guild':
                return cls.CHAT_MSG_GUILD
            case 'officer':
                return cls.CHAT_MSG_OFFICER
            case 'yell':
                return cls.CHAT_MSG_YELL
            case 'emote':
                return cls.CHAT_MSG_EMOTE
            case 'whisper':
                return cls.CHAT_MSG_WHISPER
            case 'channel' | 'custom':
                return cls.CHAT_MSG_CHANNEL
            case _:
                logging.error(f'No chat channel for this string: {channel_str}')
                return -1


class TBC(Vanilla):
    # General messages
    SMSG_GM_MESSAGECHAT = 0x03B2
    SMSG_MOTD = 0x033D
    CMSG_KEEP_ALIVE = 0x0406

    # Chat messages
    CHAT_MSG_SAY = 0x01
    CHAT_MSG_GUILD = 0x04
    CHAT_MSG_OFFICER = 0x05
    CHAT_MSG_YELL = 0x06
    CHAT_MSG_WHISPER = 0x07
    CHAT_MSG_EMOTE = 0x0A
    CHAT_MSG_TEXT_EMOTE = 0x0B
    CHAT_MSG_CHANNEL = 0x11
    CHAT_MSG_SYSTEM = 0x00
    CHAT_MSG_CHANNEL_JOIN = 0x12
    CHAT_MSG_CHANNEL_LEAVE = 0x13
    CHAT_MSG_CHANNEL_LIST = 0x14
    CHAT_MSG_CHANNEL_NOTICE = 0x15
    CHAT_MSG_CHANNEL_NOTICE_USER = 0x16

    # Channels
    CHANNEL_GUILD_RECRUITMENT = 0x19


class WotLK(TBC):
    # General messages
    SMSG_GM_MESSAGECHAT = 0x03B3
    CMSG_KEEP_ALIVE = 0x0407


class Cataclysm(WotLK):
    # General messages
    CMSG_CHAR_ENUM = 0x0502
    SMSG_CHAR_ENUM = 0x10B0
    CMSG_PLAYER_LOGIN = 0x05B1
    CMSG_LOGOUT_REQUEST = 0x0A25
    CMSG_NAME_QUERY = 0x2224
    SMSG_NAME_QUERY = 0x6E04
    CMSG_WHO = 0x6C15
    SMSG_WHO = 0x6907
    CMSG_GUILD_QUERY = 0x4426
    SMSG_GUILD_QUERY = 0x0E06
    CMSG_GUILD_ROSTER = 0x1226
    SMSG_GUILD_ROSTER = 0x3DA3
    SMSG_GUILD_EVENT = 0x0705
    SMSG_MESSAGECHAT = 0x2026
    SMSG_GM_MESSAGECHAT = 0x13B4
    CMSG_JOIN_CHANNEL = 0x0156
    SMSG_CHANNEL_NOTIFY = 0x0825
    SMSG_NOTIFICATION = 0x14A0
    CMSG_PING = 0x444D
    SMSG_AUTH_CHALLENGE = 0x4542
    CMSG_AUTH_CHALLENGE = 0x0449
    SMSG_AUTH_RESPONSE = 0x5DB6
    SMSG_LOGIN_VERIFY_WORLD = 0x2005
    SMSG_SERVER_MESSAGE = 0x6C04
    SMSG_WARDEN_DATA = 0x12E7
    CMSG_WARDEN_DATA = 0x12E8
    SMSG_INVALIDATE_PLAYER = 0x6325
    CMSG_KEEP_ALIVE = 0x0015
    SMSG_TIME_SYNC_REQ = 0x3CA4
    CMSG_TIME_SYNC_RESP = 0x3B0C
    CMSG_MESSAGECHAT_AFK = 0x0D44
    CMSG_MESSAGECHAT_BATTLEGROUND = 0x2156
    CMSG_MESSAGECHAT_CHANNEL = 0x1D44
    CMSG_MESSAGECHAT_DND = 0x2946
    CMSG_MESSAGECHAT_EMOTE = 0x1156
    CMSG_MESSAGECHAT_GUILD = 0x3956
    CMSG_MESSAGECHAT_OFFICER = 0x1946
    CMSG_MESSAGECHAT_PARTY = 0x1D46
    CMSG_MESSAGECHAT_SAY = 0x1154
    CMSG_MESSAGECHAT_WHISPER = 0x0D56
    CMSG_MESSAGECHAT_YELL = 0x3544

    overrideSMSG_MOTD = 0x0A35
    COMPRESSED_DATA_MASK = 0x8000
    WOW_CONNECTION = 0x4F57  # same hack as in mangos

    # Guild events
    GE_PROMOTED = 0x01
    GE_DEMOTED = 0x02
    GE_MOTD = 0x03
    GE_JOINED = 0x04
    GE_LEFT = 0x05
    GE_REMOVED = 0x06
    GE_SIGNED_ON = 0x10
    GE_SIGNED_OFF = 0x11

    # Channels
    CHANNEL_GUILD_RECRUITMENT = 0x00


class MoP(Cataclysm):
    # General messages
    CMSG_MESSAGECHAT_AFK = 0x0EAB
    CMSG_MESSAGECHAT_CHANNEL = 0x00BB
    CMSG_MESSAGECHAT_DND = 0x002E
    CMSG_MESSAGECHAT_EMOTE = 0x103E
    CMSG_MESSAGECHAT_GUILD = 0x0CAE
    CMSG_MESSAGECHAT_OFFICER = 0x0ABF
    CMSG_MESSAGECHAT_PARTY = 0x109A
    CMSG_MESSAGECHAT_SAY = 0x0A9A
    CMSG_MESSAGECHAT_WHISPER = 0x123E
    CMSG_MESSAGECHAT_YELL = 0x04AA
    CMSG_CHAR_ENUM = 0x00E0
    SMSG_CHAR_ENUM = 0x11C3
    CMSG_PLAYER_LOGIN = 0x158F
    CMSG_LOGOUT_REQUEST = 0x1349
    CMSG_NAME_QUERY = 0x0328
    SMSG_NAME_QUERY = 0x169B
    CMSG_GUILD_QUERY = 0x1AB6
    SMSG_GUILD_QUERY = 0x1B79
    CMSG_WHO = 0x18A3
    SMSG_WHO = 0x161B
    CMSG_GUILD_ROSTER = 0x1459
    SMSG_GUILD_ROSTER = 0x0BE0
    SMSG_MESSAGECHAT = 0x1A9A
    CMSG_JOIN_CHANNEL = 0x148E
    SMSG_CHANNEL_NOTIFY = 0x0F06
    SMSG_NOTIFICATION = 0x0C2A
    CMSG_PING = 0x0012
    SMSG_AUTH_CHALLENGE = 0x0949
    CMSG_AUTH_CHALLENGE = 0x00B2
    SMSG_AUTH_RESPONSE = 0x0ABA
    SMSG_LOGIN_VERIFY_WORLD = 0x1C0F
    SMSG_SERVER_MESSAGE = 0x0302
    SMSG_WARDEN_DATA = 0x0C0A
    CMSG_WARDEN_DATA = 0x1816
    SMSG_INVALIDATE_PLAYER = 0x102E
    CMSG_KEEP_ALIVE = 0x1A87
    SMSG_TIME_SYNC_REQ = 0x1A8F
    CMSG_TIME_SYNC_RESP = 0x01DB
    SMSG_GUILD_MOTD = 0x0B68
    SMSG_GUILD_RANKS_UPDATE = 0x0A60
    SMSG_GUILD_INVITE_ACCEPT = 0x0B69
    SMSG_GUILD_MEMBER_LOGGED = 0x0B70
    SMSG_GUILD_LEAVE = 0x0BF8
    SMSG_MOTD = 0x183B
    SMSG_COMPRESSED_DATA = 0x1568

    # Chat messages
    CHAT_MSG_ACHIEVEMENT = 0x2E
    CHAT_MSG_GUILD_ACHIEVEMENT = 0x2F


def get(expansion):
    match expansion:
        case 'Vanilla':
            return Vanilla
        case 'TBC':
            return TBC
        case 'WotLK':
            return WotLK
        case 'Cataclysm':
            return Cataclysm
        case 'MoP':
            return MoP
        case '_':
            logging.error(f'No packets for this expansion: {expansion}')
