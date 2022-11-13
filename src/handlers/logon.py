import asyncio
import hashlib
from src.common.commonclasses import Packet, Realm
from src.common.config import glob
from src.common.SRP import SRPHandler
from src.handlers.base import PacketHandler


class LogonPacketHandler(PacketHandler):
    def __init__(self, *args, **kwargs):
        self.srp_handler = None
        super().__init__(*args, **kwargs)

    @staticmethod
    def finish():
        for task in asyncio.all_tasks():
            if task.get_name() == 'logon_task':
                task.cancel()

    def handle_AUTH_LOGON_CHALLENGE(self, data):
        data.get(1)  # error code
        result = data.get(1)
        if not glob.codes.logon_auth_results.is_success(result):
            glob.logger.error(glob.codes.logon_auth_results.get_str(result))
            raise ValueError

        B = data.get(32, 'little')
        g_length = data.get(1)
        g = data.get(g_length, 'little')
        n_length = data.get(1)
        N = data.get(n_length, 'little')
        salt = data.get(32, 'little')
        data.get(16)
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
            raise ConnectionRefusedError
        proof = data.array(20)
        if proof != self.srp_handler.generate_hash_logon_proof():
            glob.logger.error('Logon proof generated by client and server differ. Something is very wrong!')
            raise ValueError
        else:
            data.get(4)  # account flag
            glob.logger.info(f'Successfully connected to logon server')
            packet = Packet(glob.codes.server_headers.REALM_LIST, int.to_bytes(0, 4, 'big'))
            self.out_queue.put_nowait(packet)

    def handle_REALM_LIST(self, data):
        realms = data.get_realms()
        target_realm = list(filter(lambda r: r.address.name.lower() == glob.logon_info.address.name.lower(), realms))[0]
        if not target_realm:
            glob.logger.error(f'Realm {glob.logon_info.realm_name} not found!')
            raise ConnectionError
        target_realm.session_key = int.to_bytes(self.srp_handler.K, 40, 'little')
        glob.realm = target_realm
        self.finish()
