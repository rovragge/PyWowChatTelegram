import hmac
from arc4 import ARC4

import src.common.config as config
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
        return self.server_crypt.decrypt(bytes(btarr))

    def encrypt(self, btarr):
        if not self.initialized:
            config.cfg.logger.debug('encrypt method called on uninitialized GameHeaderCrypt')
            return btarr
        return self.client_crypt.encrypt(bytes(btarr))

    def initialize(self, key):
        md = hmac.new(GameHeaderCrypt.SERVER_HMAC_SEED, key, 'sha1')
        server_key = md.digest()
        md = hmac.new(GameHeaderCrypt.CLIENT_HMAC_SEED, key, 'sha1')
        client_key = md.digest()
        self.server_crypt = ARC4(server_key)
        self.client_crypt = ARC4(client_key)
        self.server_crypt.encrypt(bytes(bytearray(1024)))
        self.client_crypt.decrypt(bytes(bytearray(1024)))
        self.initialized = True
