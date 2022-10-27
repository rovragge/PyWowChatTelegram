import hashlib
from src.common.utils import read_string
from src.common.commonclasses import Packet, Realm
from src.common.config import glob
from src.common.SRP import SRPHandler
from src.handlers.base import PacketHandler


class LogonPacketHandler(PacketHandler):
    def __init__(self, *args, **kwargs):
        self.srp_handler = None
        super().__init__(*args, **kwargs)

    def handle_AUTH_LOGON_CHALLENGE(self, data):
        data.get(1)  # error code
        result = data.get(1)
        if not glob.codes.logon_auth_results.is_success(result):
            glob.logger.error(glob.codes.logon_auth_results.get_str(result))
            raise ValueError

        B = int.from_bytes(data.array(32), 'little')
        g_length = data.get(1)
        g = int.from_bytes(data.array(g_length), 'little')
        n_length = data.get(1)
        N = int.from_bytes(data.array(n_length), 'little')
        salt = int.from_bytes(data.array(32), 'little')
        data.array(16)
        security_flag = data.get(1)

        self.srp_handler = SRPHandler(B, g, N, salt, security_flag)
        self.srp_handler.step1()

        buff = bytearray()
        buff += self.srp_handler.A
        buff += self.srp_handler.M

        md = hashlib.sha1(self.srp_handler.A)
        md.update(self.srp_handler.crc_hash)
        buff += md.digest()

        buff += int.to_bytes(0, 2, 'big')
        self.out_queue.put_nowait(Packet(glob.codes.server_headers.AUTH_LOGON_PROOF, buff))

    def handle_AUTH_LOGON_PROOF(self, data):
        result = data.get(1)
        if not glob.codes.logon_auth_results.is_success(result):
            glob.logger.error(glob.codes.logon_auth_results.get_str(result))
            return
        proof = data.array(20)
        if proof != self.srp_handler.generate_hash_logon_proof():
            glob.logger.error(
                'Logon proof generated by client and server differ. Something is very wrong!')
            return
        else:
            data.get(4)  # account flag
            glob.logger.info(f'Successfully logged into realm server')
            packet = Packet(glob.codes.server_headers.REALM_LIST, int.to_bytes(0, 4, 'big'))
            self.out_queue.put_nowait(packet)

    def handle_REALM_LIST(self, data):
        realms = self.parse_realm_list(data)
        target_realm = tuple(filter(lambda r: r.name.lower() == glob.connection_info.realm_name.lower(), realms))[0]
        if not target_realm:
            glob.logger.error(f'Realm {glob.connection_info.realm_name} not found!')
            return
        target_realm.session_key = int.to_bytes(self.srp_handler.K, 40, 'little')
        glob.realm = target_realm
        return 1

    @staticmethod
    def parse_realm_list(data):  # different for Vanilla/TBC+
        data.get(4)
        realms = []
        realm_count = data.get(2, endianness='little')
        for _ in range(realm_count):
            realm = Realm()
            realm.is_pvp = bool(data.get(1))
            realm.lock_flag = bool(data.get(1))
            realm.flags = data.get(1)  # offline/recommended/for newbies
            realm.name = read_string(data)
            address = read_string(data).split(':')
            realm.host = address[0]
            realm.port = int(address[1])
            realm.population = data.get(4)
            realm.num_chars = data.get(1)
            realm.timezone = data.get(1)
            realm.id = data.get(1)
            realm.build_info = data.get(5) if realm.flags & 0x04 == 0x04 else None
            realms.append(realm)
        string = 'Available realms:' + ''.join(
            [f'\n\t{realm.name} {"PvP" if realm.is_pvp else "PvE"} - {realm.host}:{realm.port}'
             for realm in realms])
        glob.logger.debug(string)
        return realms
