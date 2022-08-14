import hashlib
import secrets
from src.common.config import glob


class SRPHandler:
    def __init__(self, B, g, N, salt, security_flag):

        if security_flag:
            glob.logger.error(
                'Two factor authentication is enabled for this account. Please disable it or use another account')
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
        self.crc_hash = self.build_crc_hashes()

    def step1(self):
        self.a = int.from_bytes(secrets.token_bytes(32), 'big')
        self.A = int.to_bytes(pow(self.g, self.a, self.N), 32, 'little')

        md = hashlib.sha1(self.A)
        md.update(int.to_bytes(self.B, 32, 'little'))
        self.u = int.from_bytes(md.digest(), 'little')

        md = hashlib.sha1(bytes(f'{glob.connection_info.account}:{glob.connection_info.password}', 'utf-8'))
        p = md.digest()
        md = hashlib.sha1(int.to_bytes(self.salt, 32, 'little'))
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

        md = hashlib.sha1(bytes(glob.connection_info.account, 'utf-8'))
        t4 = md.digest()

        self.K = int.from_bytes(vk, 'little')
        t3 = int.from_bytes(hash, 'little')
        t4_correct = int.from_bytes(t4, 'little')

        md = hashlib.sha1(int.to_bytes(t3, 20, 'little'))
        md.update(int.to_bytes(t4_correct, 20, 'little'))
        md.update(int.to_bytes(self.salt, 32, 'little'))
        md.update(self.A)
        md.update(int.to_bytes(self.B, 32, 'little'))
        md.update(vk)
        self.M = md.digest()

        glob.logger.debug(
            f'SRP values (little endianness):\n\t'
            f'k = {self.k}\n\t'
            f'g = {self.g}\n\t'
            f'B = {self.B}\n\t'
            f'N = {self.N}\n\t'
            f's = {self.salt}\n\t'
            f'a = {self.a}\n\t'
            f'A = {int.from_bytes(self.A, "little")}\n\t'
            f'u = {self.u}\n\t'
            f'x = {self.x}\n\t'
            f'K = {self.K}\n\t'
            f'M = {int.from_bytes(self.M, "little")}')

    def generate_hash_logon_proof(self):
        md = hashlib.sha1(self.A)
        md.update(self.M)
        md.update(int.to_bytes(self.K, 40, 'little'))
        return md.digest()

    @staticmethod
    def build_crc_hashes():
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
            hash = hashes[glob.connection_info.platform][glob.connection_info.build]
        except KeyError:
            hash = bytearray(20)
        return hash
