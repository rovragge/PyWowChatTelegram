import hmac

import src.common.config as config

from src.common.RC4 import RC4
from src.header_crypt import Vanilla


class GameHeaderCrypt(Vanilla.GameHeaderCrypt):
    SERVER_HMAC_SEED = bytearray(b'\xcc\x98\xae\x04\xe8\x97\xea\xca\x12\xdd\xc0\x93B\x91SW')
    CLIENT_HMAC_SEED = bytearray(b'\xc2\xb3r<\xc6\xae\xd9\xb54<S\xee/Cg\xce')

    def __init__(self):
        super().__init__()
        self.client_crypt = None  # RC4
        self.server_crypt = None  # RC4

    def decrypt(self, btarr):
        if not self.initialized:
            config.cfg.logger.debug('decrypt method called on uninitialized GameHeaderCrypt')
            return btarr
        return self.server_crypt.crypt_to_bytearray(btarr)

    def encrypt(self, btarr):
        if not self.initialized:
            config.cfg.logger.debug('encrypt method called on uninitialized GameHeaderCrypt')
            return btarr
        self.client_crypt.crypt_to_bytearray(btarr)

    def initialize(self, key):
        md = hmac.new(key, GameHeaderCrypt.SERVER_HMAC_SEED, 'sha1')
        md.update(key)
        server_key = md.digest()
        md = hmac.new(key, GameHeaderCrypt.CLIENT_HMAC_SEED, 'sha1')
        md.update(key)
        client_key = md.digest()
        self.server_crypt = RC4(server_key)
        self.server_crypt.crypt_to_bytearray(bytearray(1024))
        self.client_crypt = RC4(client_key)
        self.client_crypt.crypt_to_bytearray(bytearray(1024))
        self.initialized = True
