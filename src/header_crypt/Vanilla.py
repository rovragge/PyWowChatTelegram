import src.common.config as config


class GameHeaderCrypt:
    def __init__(self):
        self.initialized = False
        self.send_i = 0
        self.send_j = 0
        self.recv_i = 0
        self.recv_j = 0
        self.key = bytearray()

    def decrypt(self, btarr):
        x = None
        if not self.initialized:
            config.glob.logger.debug('decrypt method called on uninitialized GameHeaderCrypt')
            return btarr
        for n_byte, _ in enumerate(btarr):
            self.recv_i %= len(self.key)
            x = (btarr[n_byte] - self.recv_j) ^ self.key[self.recv_i]
            self.recv_i += 1
            self.recv_j = btarr[n_byte]
            btarr[n_byte] = x
        return btarr

    def encrypt(self, btarr):
        x = None
        if not self.initialized:
            config.glob.logger.debug('encrypt method called on uninitialized GameHeaderCrypt')
            return btarr
        for n_byte, _ in enumerate(btarr):
            self.send_i %= len(self.key)
            x = (btarr[n_byte] ^ self.key[self.send_i]) + self.send_j
            self.send_i += 1
            btarr[n_byte] = x
            self.send_j = x
        return btarr

    def initialize(self, key):
        self.key = key
        self.send_i = 0
        self.send_j = 0
        self.recv_i = 0
        self.recv_i = 0
        self.initialized = True
