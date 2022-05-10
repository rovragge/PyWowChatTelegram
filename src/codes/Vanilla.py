import src.common.config as config


class CodeCollection:

    @classmethod
    def get_str(cls, code):
        for attr_name in dir(cls):
            if getattr(cls, attr_name) == code:
                string = attr_name
                break
        else:
            config.cfg.logger.error(f'Cant find string for code {code} in class {cls.__name__}')
            return 'Unknown'
        string = string.lower().replace('_', ' ')
        string = string[0].upper() + string[1:]
        return string

    @classmethod
    def get_from_str(cls, string):
        attr_name = string.upper().replace(' ', '_')
        attr = getattr(cls, attr_name)
        if not attr:
            config.cfg.logger.error(f'No record with name {string} for class {cls.__name__}')
            return -1
        return attr


class GameAuthResults(CodeCollection):
    OK = 0x0C
    FAILED = 0x0D
    REJECT = 0x0E
    BAD_SERVER_PROOF = 0x0F
    UNAVAILABLE = 0x10
    SYSTEM_ERROR = 0x11
    BILLING_ERROR = 0x12
    BILLING_EXPIRED = 0x13
    VERSION_MISMATCH = 0x14
    UNKNOWN_ACCOUNT = 0x15
    INCORRECT_PASSWORD = 0x16
    SESSION_EXPIRED = 0x17
    SERVER_SHUTTING_DOWN = 0x18
    ALREADY_LOGGING_IN = 0x19
    LOGIN_SERVER_NOT_FOUND = 0x1A
    WAIT_QUEUE = 0x1B
    BANNED = 0x1C
    ALREADY_ONLINE = 0x1D
    NO_TIME = 0x1E
    DB_BUSY = 0x1F
    SUSPENDED = 0x20
    PARENTAL_CONTROL = 0x21


class RealmServerAuthResults(CodeCollection):
    SUCCESS = 0x00
    FAIL_BANNED = 0x03
    FAIL_UNKNOWN_ACCOUNT = 0x04
    FAIL_INCORRECT_PASSWORD = 0x05
    FAIL_ALREADY_ONLINE = 0x06
    FAIL_NO_TIME = 0x07
    FAIL_DB_BUSY = 0x08
    FAIL_VERSION_INVALID = 0x09
    FAIL_VERSION_UPDATE = 0x0A
    FAIL_INID_SERVER = 0x0B
    FAIL_SUSPENDED = 0x0C
    FAIL_FAIL_NOACCESS = 0x0D
    SUCCESS_SURVEY = 0x0E
    FAIL_PARENTCONTROL = 0x0F
    FAIL_LOCKED_ENFORCED = 0x10
    FAIL_TRIAL_ENDED = 0x11
    FAIL_USE_BATTLENET = 0x12
    FAIL_ANTI_INDULGENCE = 0x13
    FAIL_EXPIRED = 0x14
    FAIL_NO_GAME_ACCOUNT = 0x15
    FAIL_CHARGEBACK = 0x16
    FAIL_INTERNET_GAME_ROOM_WITHOUT_BNET = 0x17
    FAIL_GAME_ACCOUNT_LOCKED = 0x18
    FAIL_UNLOCKABLE_LOCK = 0x19
    FAIL_CONVERSION_REQUIRED = 0x20
    FAIL_DISCONNECTED = 0xFF

    @classmethod
    def is_success(cls, result):
        return result == cls.SUCCESS or result == cls.SUCCESS_SURVEY


class ServerMessages(CodeCollection):
    SHUTDOWN_TIME = 0x01
    RESTART_TIME = 0x02
    CUSTOM = 0x03
    SHUTDOWN_CANCELLED = 0x04
    RESTART_CANCELLED = 0x05


class CharClasses(CodeCollection):
    WARRIOR = 0x01
    PALADIN = 0x02
    HUNTER = 0x03
    ROGUE = 0x04
    PRIEST = 0x05
    DEATH_KNIGHT = 0x06
    SHAMAN = 0x07
    MAGE = 0x08
    WARLOCK = 0x09
    MONK = 0x0A
    DRUID = 0x0B


class CharRaces(CodeCollection):
    HUMAN = 0x01
    ORC = 0x02
    DWARF = 0x03
    NIGHTELF = 0x04
    UNDEAD = 0x05
    TAUREN = 0x06
    GNOME = 0x07
    TROLL = 0x08
    GOBLIN = 0x09
    BLOODELF = 0x0A
    DRAENEI = 0x0B
    WORGEN = 0x16
    PANDAREN_NEUTRAL = 0x18
    PANDAREN_ALLIANCE = 0x19
    PANDAREN_HORDE = 0x1A

    @classmethod
    def get_language(cls, race):
        match race:
            case cls.ORC | cls.UNDEAD | cls.TAUREN | cls.TROLL | cls.BLOODELF | cls.GOBLIN | cls.PANDAREN_HORDE:
                return 0x01  # orcish
            case cls.PANDAREN_NEUTRAL:
                return 0x2A
            case _:
                return 0x07  # common


class CharGenders(CodeCollection):
    MALE = 0
    FEMALE = 1
    NONE = 2


class CommonChannels(CodeCollection):
    GENERAL = 0x01
    TRADE = 0x02
    LOCAL_DEFENSE = 0x16
    WORLD_DEFENSE = 0x17
    GUILD_RECRUITMENT = 0x00
    LOOKING_FOR_GROUP = 0x1A


class ChatChannels(CodeCollection):
    SAY = 0x00
    GUILD = 0x03
    OFFICER = 0x04
    YELL = 0x05
    WHISPER = 0x06
    EMOTE = 0x08
    TEXT_EMOTE = 0x09
    CHANNEL = 0x0E
    SYSTEM = 0x0A
    CHANNEL_JOIN = 0x0F
    CHANNEL_LEAVE = 0x10
    CHANNEL_LIST = 0x11
    CHANNEL_NOTICE = 0x12
    CHANNEL_NOTICE_USER = 0x13
    ACHIEVEMENT = 0x30
    GUILD_ACHIEVEMENT = 0x31


class ChatEvents(CodeCollection):
    JOINED_NOTICE = 0x00
    LEFT_NOTICE = 0x01
    YOU_JOINED_NOTICE = 0x02
    YOU_LEFT_NOTICE = 0x03
    WRONG_PASSWORD_NOTICE = 0x04
    NOT_MEMBER_NOTICE = 0x05
    NOT_MODERATOR_NOTICE = 0x06
    PASSWORD_CHANGED_NOTICE = 0x07
    OWNER_CHANGED_NOTICE = 0x08
    PLAYER_NOT_FOUND_NOTICE = 0x09
    NOT_OWNER_NOTICE = 0x0A
    CHANNEL_OWNER_NOTICE = 0x0B
    MODE_CHANGE_NOTICE = 0x0C
    ANNOUNCEMENTS_ON_NOTICE = 0x0D
    ANNOUNCEMENTS_OFF_NOTICE = 0x0E
    MODERATION_ON_NOTICE = 0x0F
    MODERATION_OFF_NOTICE = 0x10
    MUTED_NOTICE = 0x11
    PLAYER_KICKED_NOTICE = 0x12
    BANNED_NOTICE = 0x13
    PLAYER_BANNED_NOTICE = 0x14
    PLAYER_UNBANNED_NOTICE = 0x15
    PLAYER_NOT_BANNED_NOTICE = 0x16
    PLAYER_ALREADY_MEMBER_NOTICE = 0x17
    INVITE_NOTICE = 0x18
    INVITE_WRONG_FACTION_NOTICE = 0x19
    WRONG_FACTION_NOTICE = 0x1A
    INVALID_NAME_NOTICE = 0x1B
    NOT_MODERATED_NOTICE = 0x1C
    PLAYER_INVITED_NOTICE = 0x1D
    PLAYER_INVITE_BANNED_NOTICE = 0x1E
    THROTTLED_NOTICE = 0x1F
    NOT_IN_AREA_NOTICE = 0x20
    NOT_IN_LFG_NOTICE = 0x21
    VOICE_ON_NOTICE = 0x22
    VOICE_OFF_NOTICE = 0x23


class GuildEvents(CodeCollection):
    PROMOTED = 0x00
    DEMOTED = 0x01
    MOTD = 0x02
    JOINED = 0x03
    LEFT = 0x04
    REMOVED = 0x05
    SIGNED_ON = 0x0C
    SIGNED_OFF = 0x0D


class ClientHeaders(CodeCollection):
    AUTH_CHALLENGE = 0x01ED
    CHAR_ENUM = 0x37
    PLAYER_LOGIN = 0x3D
    LOGOUT_REQUEST = 0x4B
    NAME_QUERY = 0x50
    GUILD_QUERY = 0x54
    GUILD_ROSTER = 0x89
    MESSAGECHAT = 0x95
    JOIN_CHANNEL = 0x97
    PING = 0x01DC
    GROUP_INVITE = 0x06E
    TIME_SYNC_RESP = 0x039
    WARDEN_DATA = 0x02E7
    WHO = 0x62


class ServerHeaders(CodeCollection):
    AUTH_CHALLENGE = 0x01EC
    AUTH_RESPONSE = 0x01EE
    CHANNEL_NOTIFY = 0x99
    CHAR_ENUM = 0x3B
    NAME_QUERY = 0x51
    GUILD_QUERY = 0x55
    INVALIDATE_PLAYER = 0x031C
    GROUP_INVITE = 0x06F
    LOGIN_VERIFY_WORLD = 0x0236
    TIME_SYNC_REQ = 0x0390
    SERVER_MESSAGE = 0x0291
    GUILD_ROSTER = 0x8A
    GUILD_EVENT = 0x92
    MESSAGECHAT = 0x96
    NOTIFICATION = 0x01CB
    WARDEN_DATA = 0x02E6
    WHO = 0x63


class RealmHeaders(CodeCollection):
    AUTH_LOGON_CHALLENGE = 0x00
    AUTH_LOGON_PROOF = 0x01
    REALM_LIST = 0x10


class Codes:
    classes = CharClasses
    races = CharRaces
    genders = CharGenders
    game_auth_results = GameAuthResults
    realm_server_auth_results = RealmServerAuthResults
    client_headers = ClientHeaders
    realm_headers = RealmHeaders
    server_headers = ServerHeaders
    guild_events = GuildEvents
    servers_messages = ServerMessages
    chat_events = ChatEvents
    chat_channels = ChatChannels
    common_channels = CommonChannels
