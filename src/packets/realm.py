CMD_AUTH_LOGON_CHALLENGE = 0x00
CMD_AUTH_LOGON_PROOF = 0x01
CMD_REALM_LIST = 0x10


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
                return 'Incorrect password'
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
