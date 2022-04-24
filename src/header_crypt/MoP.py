from src.header_crypt import WotLK


class GameHeaderCrypt(WotLK.GameHeaderCrypt):
    SERVER_HMAC_SEED = bytearray(b'\x08\xf1\x95\x9fG\xe5\xd2\xdb\xa1=w\x8f?>\xe7\x00')
    CLIENT_HMAC_SEED = bytearray(b'@\xaa\xd3\x92&qCG:1\x08\xa6\xe7\xdc\x98*')
