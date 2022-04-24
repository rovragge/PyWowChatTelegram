import hmac

from src.header_crypt import Vanilla


class GameHeaderCrypt(Vanilla.GameHeaderCrypt):
    HMAC_SEED = [b'8', b'\xa7', b'\x83', b'\x15', b'\xf8', b'\x92', b'%', b'0', b'q', b'\x98', b'game', b'\xb1',
                 b'\x8c', b'\x04', b'\xe2', b'\xaa']

    def initialize(self, key):
        super().initialize(key)
        md = hmac.new(key, GameHeaderCrypt.HMAC_SEED, 'sha1')
        md.update(key)
        self.key = md.digest()
