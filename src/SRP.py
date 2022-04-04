import hashlib
import os


class SRPHandler:
    def __init__(self, B, g, N, salt, unk_3, security_flag, cfg):

        if security_flag:
            print('Two factor authentication is enabled for this account. Please disable it or use another account')
            raise ValueError

        # computed values
        self.a = None
        self.A = None
        self.u = None
        self.x = None
        self.K = None
        self.M = None
        # provided values
        self.k = 3
        self.B = B
        self.g = g
        self.N = N
        self.salt = salt
        self.unk3 = unk_3
        self.cfg = cfg
        self.crc_hash = self.build_crc_hashes()

    @staticmethod
    def get_random_of_length(nbytes):
        offset = (nbytes * 8) - 1
        return int.from_bytes(os.urandom(nbytes), 'big') | (1 << offset)

    def step1(self):
        self.a = self.get_random_of_length(32)
        self.A = int.to_bytes(pow(self.g, self.a, self.N), 32, 'little')

        md = hashlib.sha1(self.A)
        md.update(int.to_bytes(self.B, 32, 'little'))
        self.u = int.from_bytes(md.digest(), 'little')

        md = hashlib.sha1(bytes(f'{self.cfg.get_account()}:{self.cfg.get_password()}', 'utf-8'))
        p = md.digest()
        md = hashlib.sha1(self.salt)
        md.update(p)
        self.x = int.from_bytes(md.digest(), 'little')

        S = int.to_bytes(pow((self.B - self.k * pow(self.g, self.x, self.N)), (self.a + self.u * self.x), self.N), 32,
                         'little')
        t1 = bytearray(16)
        t2 = bytearray(16)
        vk = bytearray(40)

        for i in range(16):
            t1[i] = S[i * 2]
            t2[i] = S[i * 2 + 1]

        md = hashlib.sha1(t1)
        digest = md.digest()
        for i in range(20):
            vk[i * 2] = digest[i]

        md = hashlib.sha1(t2)
        digest = md.digest()
        for i in range(20):
            vk[i * 2 + 1] = digest[i]

        md = hashlib.sha1(int.to_bytes(self.N, 32, 'little'))
        hash = bytearray(md.digest())

        md = hashlib.sha1(int.to_bytes(self.g, 1, 'little'))
        digest = md.digest()
        for i in range(20):
            hash[i] = (hash[i] ^ digest[i])

        md = hashlib.sha1(bytes(self.cfg.get_account(), 'utf-8'))
        t4 = md.digest()

        self.K = int.from_bytes(vk, 'little')
        t3 = int.from_bytes(hash, 'little')
        t4_correct = int.from_bytes(t4, 'little')

        md = hashlib.sha1(int.to_bytes(t3, 20, 'little'))
        md.update(int.to_bytes(t4_correct, 20, 'little'))
        md.update(self.salt)
        md.update(self.A)
        md.update(int.to_bytes(self.B, 32, 'little'))
        md.update(vk)
        self.M = md.digest()

    def generate_hash_logon_proof(self):
        md = hashlib.sha1(self.A)
        md.update(self.M)
        md.update(int.to_bytes(self.K, 40, 'little'))
        return md.digest()

    def build_crc_hashes(self):
        hashes = {
            'Mac': {
                5875: b'\x8d\x17<\xc3\x81\x96\x1e\xeb\xab\xf36\xf5\xe6g[\x10\x1b\xb5\x13\xe5',
                8606: b'\xd8\xb0\xec\xfeSK\xc1\x13\x1e\x19\xba\xd1\xd4\xc0\xe8\x13\xee\xe4\x99O',
                12340: b'\xb7\x06\xd1?\xf2\xf4\x01\x889r\x94a\xe3\xf8\xa0\xe2\xb5\xfd\xc04'
            },
            'Win': {
                5875: b'\x95\xed\xb2|x#\xb3c\xcb\xdd\xabV\xa3\x92\xe7\xcbs\xfc\xca ',
                8606: b'1\x9a\xfa\xa3\xf2U\x96\x82\xf9\xffe\x8b\xe0\x14V%_Eo\xb1',
                12340: b'\xcd\xcb\xbdQ\x881^kM\x19D\x9dI-\xbc\xfa\xf1V\xa3G'
            }
        }
        try:
            hash = hashes[self.cfg.get_platform()][self.cfg.get_build()]
        except KeyError:
            hash = bytearray(20)
        return hash
