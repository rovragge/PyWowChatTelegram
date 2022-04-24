class AuthPackets:
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

    @staticmethod
    def is_success(result):
        return result == AuthPackets.SUCCESS or result == AuthPackets.SUCCESS_SURVEY

    @staticmethod
    def get_message(result):
        match result:
            case AuthPackets.SUCCESS:
                return 'Success!'
            case AuthPackets.FAIL_UNKNOWN_ACCOUNT:
                return 'Unknown account'
            case AuthPackets.FAIL_INCORRECT_PASSWORD:
                return 'Incorrect password'
            case AuthPackets.FAIL_BANNED:
                return 'Your account has been banned!'
            case AuthPackets.FAIL_INCORRECT_PASSWORD:
                return 'Incorrect username or password!'
            case AuthPackets.FAIL_ALREADY_ONLINE:
                return 'Your account is already online. Wait a moment and try again!'
            case AuthPackets.FAIL_VERSION_INVALID:
                return 'Invalid game version for this server!'
            case AuthPackets.FAIL_SUSPENDED:
                return 'Your account has been suspended!'
            case AuthPackets.FAIL_FAIL_NOACCESS:
                return 'Login failed! You do not have access to this server!'
            case _:
                return 'Unknown auth result!'

class RealmPackets:
    CMD_AUTH_LOGON_CHALLENGE = 0x00
    CMD_AUTH_LOGON_PROOF = 0x01
    CMD_REALM_LIST = 0x10
    AUTH = AuthPackets
