# used for warden and wotlk header encryption

class RC4:
    SBOX_LENGTH = 256

    def __init__(self, key):
        self.sbox = self.init_sbox(key)
        self.i = 0
        self.j = 0

    def init_sbox(self, key):
        sbox = [i for i in range(RC4.SBOX_LENGTH)]
        j = 0
        for i in range(RC4.SBOX_LENGTH):
            j = (j + sbox[i] + key[i % len(key)] + RC4.SBOX_LENGTH) % RC4.SBOX_LENGTH
            sbox[i], sbox[j] = sbox[j], sbox[i]  # swap
        return sbox

    def crypt_to_bytearray(self, btarr):
        code = bytearray(len(btarr))
        for n, _ in enumerate(btarr):
            self.i = (self.i + 1) % RC4.SBOX_LENGTH
            self.j = (self.j + self.sbox[self.i]) % RC4.SBOX_LENGTH
            self.sbox[self.i], self.sbox[self.j] = self.sbox[self.j], self.sbox[self.i]  # swap
            rand = self.sbox[(self.sbox[self.i] + self.sbox[self.j]) % RC4.SBOX_LENGTH]
            code[n] = rand ^ btarr[n]
        return code

    def crypt(self, data, length=0):
        if length:
            return self.crypt_to_bytearray(data[:length])
        return self.crypt_to_bytearray(data)
