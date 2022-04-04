class GamePackets:
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
    CMSG_TIME_SYNC_RESP = 0x0391


class ChatEvents:
    # is_Vanilla = wow_chat_config.getExpansion() == wow_expansion.Vanilla
    # is_MoP = wow_chat_config.getExpansion() == wow_expansion.Vanilla
    is_Vanilla = False
    is_MoP = False
    CHAT_MSG_SAY = bytes(0x00 if is_Vanilla else 0x01)
    CHAT_MSG_GUILD = bytes(0x03 if is_Vanilla else 0x04)
    CHAT_MSG_OFFICER = bytes(0x04 if is_Vanilla else 0x05)
    CHAT_MSG_YELL = bytes(0x05 if is_Vanilla else 0x06)
    CHAT_MSG_WHISPER = bytes(0x06 if is_Vanilla else 0x07)
    CHAT_MSG_EMOTE = bytes(0x08 if is_Vanilla else 0x0A)
    CHAT_MSG_TEXT_EMOTE = bytes(0x09 if is_Vanilla else 0x0B)
    CHAT_MSG_CHANNEL = bytes(0x0E if is_Vanilla else 0x11)
    CHAT_MSG_SYSTEM = bytes(0x0A if is_Vanilla else 0x00)
    CHAT_MSG_CHANNEL_JOIN = bytes(0x0F if is_Vanilla else 0x12)
    CHAT_MSG_CHANNEL_LEAVE = bytes(0x10 if is_Vanilla else 0x13)
    CHAT_MSG_CHANNEL_LIST = bytes(0x11 if is_Vanilla else 0x14)
    CHAT_MSG_CHANNEL_NOTICE = bytes(0x12 if is_Vanilla else 0x15)
    CHAT_MSG_CHANNEL_NOTICE_USER = bytes(0x13 if is_Vanilla else 0x16)
    CHAT_MSG_ACHIEVEMENT = bytes(0x2E if is_MoP else 0x30)
    CHAT_MSG_GUILD_ACHIEVEMENT = bytes(0x2F if is_MoP else 0x31)

    @staticmethod
    def parse(tp):
        match tp.lower():
            case 'system':
                return ChatEvents.CHAT_MSG_SYSTEM
            case 'say':
                return ChatEvents.CHAT_MSG_SAY
            case 'guild':
                return ChatEvents.CHAT_MSG_GUILD
            case 'officer':
                return ChatEvents.CHAT_MSG_OFFICER
            case 'yell':
                return ChatEvents.CHAT_MSG_YELL
            case 'emote':
                return ChatEvents.CHAT_MSG_EMOTE
            case 'whisper':
                return ChatEvents.CHAT_MSG_WHISPER
            case 'channel' | 'custom':
                return ChatEvents.CHAT_MSG_CHANNEL
            case _:
                return bytes(-1)

    @staticmethod
    def value_of(tp):
        match tp:
            case ChatEvents.CHAT_MSG_SAY:
                return 'Say'
            case ChatEvents.CHAT_MSG_GUILD:
                return 'Guild'
            case ChatEvents.CHAT_MSG_OFFICER:
                return 'Offcier'
            case ChatEvents.CHAT_MSG_YELL:
                return 'Yell'
            case ChatEvents.CHAT_MSG_WHISPER:
                return 'Whisper'
            case ChatEvents.CHAT_MSG_EMOTE | ChatEvents.CHAT_MSG_TEXT_EMOTE:
                return 'Emote'
            case ChatEvents.CHAT_MSG_CHANNEL:
                return 'Channel'
            case ChatEvents.CHAT_MSG_SYSTEM:
                return 'System'
            case _:
                return 'Unknown channel'


class GuildEvents:
    # is_Cataclysm = wow_chat_config.getExpansion() == wow_expansion.Cataclysm
    is_Cataclysm = False
    GE_PROMOTED = 0x01 if is_Cataclysm else 0x00
    GE_DEMOTED = 0x02 if is_Cataclysm else 0x01
    GE_MOTD = 0x03 if is_Cataclysm else 0x02
    GE_JOINED = 0x04 if is_Cataclysm else 0x03
    GE_LEFT = 0x05 if is_Cataclysm else 0x04
    GE_REMOVED = 0x06 if is_Cataclysm else 0x05
    GE_SIGNED_ON = 0x10 if is_Cataclysm else 0x0C
    GE_SIGNED_OFF = 0x11 if is_Cataclysm else 0x0D


class Races:
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

    @staticmethod
    def get_language(race):
        match race:
            case Races.RACE_ORC | Races.RACE_UNDEAD | Races.RACE_TAUREN | Races.RACE_TROLL \
                 | Races.RACE_BLOODELF | Races.RACE_GOBLIN | Races.RACE_PANDAREN_HORDE:
                return 0x01  # orcish
            case Races.RACE_PANDAREN_NEUTRAL:
                return 0x2A
            case _:
                return 0x07  # common

    @staticmethod
    def value_of(char_race):
        match char_race:
            case Races.RACE_HUMAN:
                return 'Human'
            case Races.RACE_ORC:
                return 'Orc'
            case Races.RACE_DWARF:
                return 'Dwarf'
            case Races.RACE_NIGHTELF:
                return 'Night Elf'
            case Races.RACE_UNDEAD:
                return 'Undead'
            case Races.RACE_TAUREN:
                return 'Tauren'
            case Races.RACE_GNOME:
                return 'Gnome'
            case Races.RACE_TROLL:
                return 'Troll'
            case Races.RACE_GOBLIN:
                return 'Goblin'
            case Races.RACE_BLOODELF:
                return 'Blood Elf'
            case Races.RACE_DRAENEI:
                return 'Draenei'
            case Races.RACE_WORGEN:
                return 'Worgen'
            case Races.RACE_PANDAREN_NEUTRAL:
                return 'Pandaren'
            case Races.RACE_PANDAREN_ALLIANCE:
                return 'Allince Pandaren'
            case Races.RACE_PANDAREN_HORDE:
                return 'Horde Pandaren'
            case _:
                return 'Unknown race'


class Classes:
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

    @staticmethod
    def value_of(char_class):
        match char_class:
            case Classes.CLASS_WARRIOR:
                return 'Warrior'
            case Classes.CLASS_PALADIN:
                return 'Paladin'
            case Classes.CLASS_HUNTER:
                return 'Hunter'
            case Classes.CLASS_ROGUE:
                return 'Rogue'
            case Classes.CLASS_DEATH_KNIGHT:
                return 'Death Knight'
            case Classes.CLASS_PRIEST:
                return 'Priest'
            case Classes.CLASS_SHAMAN:
                return 'Shaman'
            case Classes.CLASS_MAGE:
                return 'Mage'
            case Classes.CLASS_WARLOCK:
                return 'Warlock'
            case Classes.CLASS_MONK:
                return 'Monk'
            case Classes.CLASS_DRUID:
                return 'Druid'
            case _:
                return 'Unknown class'


class Genders:
    GENDER_MALE = 0
    GENDER_FEMALE = 1
    GENDER_NONE = 2

    @staticmethod
    def value_of(char_gender):
        match char_gender:
            case Genders.GENDER_MALE:
                return 'Male'
            case Genders.GENDER_FEMALE:
                return 'Female'
            case _:
                return 'Unknown gender'


class AuthResponseCodes:
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

    @staticmethod
    def get_message(auth_result):
        match auth_result:
            case AuthResponseCodes.AUTH_OK:
                return 'Success!'
            case AuthResponseCodes.AUTH_UNKNOWN_ACCOUNT:
                return 'Incorrect username!'
            case AuthResponseCodes.AUTH_INCORRECT_PASSWORD:
                return 'Incorrect password!'
            case AuthResponseCodes.AUTH_VERSION_MISMATCH:
                return 'Invalid game version for this server'
            case AuthResponseCodes.AUTH_BANNED:
                return 'Your account has been banned!'
            case AuthResponseCodes.AUTH_ALREADY_LOGGING_IN | AuthResponseCodes.AUTH_ALREADY_ONLINE:
                return 'Your account is already online! Log it off or wait a minute if already logging off'
            case AuthResponseCodes.AUTH_SUSPENDED:
                return 'Your account has been suspended!'
            case _:
                return f'Failed to login to game server! authResult: {auth_result}'


class ChatNotify:
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


class ServerMessageType:
    SERVER_MSG_SHUTDOWN_TIME = 0x01
    SERVER_MSG_RESTART_TIME = 0x02
    SERVER_MSG_CUSTOM = 0x03
    SERVER_MSG_SHUTDOWN_CANCELLED = 0x04
    SERVER_MSG_RESTART_CANCELLED = 0x05


class ChatChannelIds:
    GENERAL = 0x01
    TRADE = 0x02
    LOCAL_DEFENSE = 0x16
    WORLD_DEFENSE = 0x17
    LOOKING_FOR_GROUP = 0x1A
    # GUILD_RECRUITMENT = 0x19 if wow_chat_config.getExpansion() in (wow_expansion.TBC, wow_expansion.WotLK) else 0x00
    GUILD_RECRUITMENT = 0x19

    @staticmethod
    def get_id(channel):
        match channel.split(' ')[0].lower():
            case 'general':
                return ChatChannelIds.GENERAL
            case 'trade':
                return ChatChannelIds.TRADE
            case 'localdefense':
                return ChatChannelIds.LOCAL_DEFENSE
            case 'worlddefense':
                return ChatChannelIds.WORLD_DEFENSE
            case 'guildrecruitment':
                return ChatChannelIds.GUILD_RECRUITMENT
            case 'lookingforgroup':
                return ChatChannelIds.LOOKING_FOR_GROUP
            case _:
                return 0x00


class AuthResult:
    WOW_SUCCESS = 0x00
    WOW_FAIL_BANNED = 0x03
    WOW_FAIL_UNKNOWN_ACCOUNT = 0x04
    WOW_FAIL_INCORRECT_PASSWORD = 0x05
    WOW_FAIL_ALREADY_ONLINE = 0x06
    WOW_FAIL_NO_TIME = 0x07
    WOW_FAIL_DB_BUSY = 0x08
    WOW_FAIL_VERSION_INVALID = 0x09
    WOW_FAIL_VERSION_UPDATE = 0x0A
    WOW_FAIL_INID_SERVER = 0x0B
    WOW_FAIL_SUSPENDED = 0x0C
    WOW_FAIL_FAIL_NOACCESS = 0x0D
    WOW_SUCCESS_SURVEY = 0x0E
    WOW_FAIL_PARENTCONTROL = 0x0F
    WOW_FAIL_LOCKED_ENFORCED = 0x10
    WOW_FAIL_TRIAL_ENDED = 0x11
    WOW_FAIL_USE_BATTLENET = 0x12
    WOW_FAIL_ANTI_INDULGENCE = 0x13
    WOW_FAIL_EXPIRED = 0x14
    WOW_FAIL_NO_GAME_ACCOUNT = 0x15
    WOW_FAIL_CHARGEBACK = 0x16
    WOW_FAIL_INTERNET_GAME_ROOM_WITHOUT_BNET = 0x17
    WOW_FAIL_GAME_ACCOUNT_LOCKED = 0x18
    WOW_FAIL_UNLOCKABLE_LOCK = 0x19
    WOW_FAIL_CONVERSION_REQUIRED = 0x20
    WOW_FAIL_DISCONNECTED = 0xFF

    @staticmethod
    def is_success(auth_result):
        return auth_result == AuthResult.WOW_SUCCESS or auth_result == AuthResult.WOW_SUCCESS_SURVEY

    @staticmethod
    def get_message(auth_result):
        match auth_result:
            case AuthResult.WOW_SUCCESS:
                return 'Success!'
            case AuthResult.WOW_FAIL_UNKNOWN_ACCOUNT:
                return 'Unknown account'
            case AuthResult.WOW_FAIL_INCORRECT_PASSWORD:
                return  'Incorrect password'
            case AuthResult.WOW_FAIL_BANNED:
                return 'Your account has been banned!'
            case AuthResult.WOW_FAIL_INCORRECT_PASSWORD:
                return 'Incorrect username or password!'
            case AuthResult.WOW_FAIL_ALREADY_ONLINE:
                return 'Your account is already online. Wait a moment and try again!'
            case AuthResult.WOW_FAIL_VERSION_INVALID:
                return 'Invalid game version for this server!'
            case AuthResult.WOW_FAIL_SUSPENDED:
                return 'Your account has been suspended!'
            case AuthResult.WOW_FAIL_FAIL_NOACCESS:
                return 'Login failed! You do not have access to this server!'
            case _:
                return 'Unknown auth result!'


class RealmPackets:
    CMD_AUTH_LOGON_CHALLENGE = 0x00
    CMD_AUTH_LOGON_PROOF = 0x01
    CMD_REALM_LIST = 0x10
