import hashlib
import re
import logging
import PyByteBuffer
import asyncio

import connector
import packets.realm
import SRP


class RealmConnector(connector.Connector):
    def __init__(self, cfg):
        super().__init__(cfg)
        self.srp_handler = None

    async def connect(self):
        host, port = self.cfg.parse_realm_list()
        logging.info(f'Connecting to realm server: {host}:{port}')
        self.reader, self.writer = await asyncio.open_connection(host, port)
        packet = self.get_initial_packet()
        await self.send(packet, is_realm_packet=True)

        data = await self.reader.read(128)  # logon challenge
        packet = self.assign_packet_handler(self.decode(data))
        await self.send(packet, is_realm_packet=True)

        data = await self.reader.read(32)  # logon proof
        packet = self.assign_packet_handler(self.decode(data))
        await self.send(packet, is_realm_packet=True)

        data = await self.reader.read(1024)  # realmlist
        realm = self.assign_packet_handler(self.decode(data))
        self.writer.close()
        return realm

    def decode(self, data):
        size = 0
        in_buff = PyByteBuffer.ByteBuffer.wrap(data)
        if not in_buff.remaining:
            return
        packet_id = in_buff.get(1)
        match packet_id:
            case packets.realm.CMD_AUTH_LOGON_CHALLENGE:
                if in_buff.remaining < 2:
                    return
                saved_position = in_buff.position
                in_buff.get(1)
                size = 118 if packets.realm.AuthResult.is_success(in_buff.get(1)) else 2
                self.reset_position(saved_position, in_buff)
            case packets.realm.CMD_AUTH_LOGON_PROOF:
                if in_buff.remaining < 1:
                    return
                saved_position = in_buff.position
                if packets.realm.AuthResult.is_success(in_buff.get(1)):
                    size = 25 if self.cfg.get_expansion() == 'Vanilla' else 31
                else:
                    size = 1 if not in_buff.remaining else 3
                self.reset_position(saved_position, in_buff)
            case packets.realm.CMD_REALM_LIST:
                if in_buff.remaining < 2:
                    return
                size = in_buff.get(2, endianness='little')
        if size > in_buff.remaining:
            return
        packet = connector.Packet(packet_id, in_buff.slice().array(size))
        logging.debug(f'RECV REALM PACKET: {packet}')
        return packet

    def assign_packet_handler(self, packet):
        if not isinstance(packet, connector.Packet):
            logging.error(f'packet is instance of {type(packet)}')
            return
        match packet.id:
            case packets.realm.CMD_AUTH_LOGON_CHALLENGE:
                return self.handle_CMD_AUTH_LOGON_CHALLENGE(packet)
            case packets.realm.CMD_AUTH_LOGON_PROOF:
                return self.handle_CMD_AUTH_LOGON_PROOF(packet)
            case packets.realm.CMD_REALM_LIST:
                return self.handle_CMD_REALM_LIST(packet)
            case _:
                logging.error(f'Received packet {packet.id:04X} in unexpected logonState')

    def get_initial_packet(self):
        version = [bytes(x, 'utf-8') for x in str(self.cfg.get_version()).split('.')]
        account = bytes(self.cfg.get_account(), 'utf-8')
        buffer = PyByteBuffer.ByteBuffer.allocate(100)
        buffer.put(3 if self.cfg.get_expansion() == 'Vanilla' else 8)
        buffer.put(30 + len(account), endianness='little', size=2)
        buffer.put(self.str_to_int('WoW'))
        buffer.put(0)
        buffer.put(version[0])
        buffer.put(version[1])
        buffer.put(version[2])
        buffer.put(self.cfg.get_build(), endianness='little')
        buffer.put(self.str_to_int('x86'), endianness='little', size=4)
        buffer.put(self.str_to_int(self.cfg.get_platform()), endianness='little', size=4)
        buffer.put(self.str_to_int(self.cfg.get_locale()), endianness='little', size=4)
        buffer.put(0)
        buffer.put(127, size=4)
        buffer.put(0)
        buffer.put(0)
        buffer.put(1)
        buffer.put(len(account))
        buffer.put(account)
        buffer.strip()
        buffer.rewind()
        packet = connector.Packet(packets.realm.CMD_AUTH_LOGON_CHALLENGE, buffer.array())
        return packet

    def handle_CMD_AUTH_LOGON_CHALLENGE(self, packet):
        byte_buff = PyByteBuffer.ByteBuffer.wrap(packet.data)
        error_code = byte_buff.get(1)
        result = byte_buff.get(1)
        if not packets.realm.AuthResult.is_success(result):
            logging.error(packets.realm.AuthResult.get_message(result))
            raise ValueError

        B = int.from_bytes(byte_buff.array(32), 'little')
        g_length = byte_buff.get(1)
        g = int.from_bytes(byte_buff.array(g_length), 'little')
        n_length = byte_buff.get(1)
        N = int.from_bytes(byte_buff.array(n_length), 'little')
        salt = int.from_bytes(byte_buff.array(32), 'little')
        unk_3 = byte_buff.array(16)
        security_flag = byte_buff.get(1)

        self.srp_handler = SRP.SRPHandler(B, g, N, salt, security_flag, self.cfg)
        self.srp_handler.step1()

        buff = bytearray()
        buff += self.srp_handler.A
        buff += self.srp_handler.M

        md = hashlib.sha1(self.srp_handler.A)
        md.update(self.srp_handler.crc_hash)
        buff += md.digest()

        buff += int.to_bytes(0, 2, 'big')
        packet = connector.Packet(packets.realm.CMD_AUTH_LOGON_PROOF, buff)
        return packet

    def handle_CMD_AUTH_LOGON_PROOF(self, packet):
        byte_buff = PyByteBuffer.ByteBuffer.wrap(packet.data)
        result = byte_buff.get(1)
        if not packets.realm.AuthResult.is_success(result):
            logging.error(packets.realm.AuthResult.get_message(result))
            return
        proof = byte_buff.array(20)
        if proof != self.srp_handler.generate_hash_logon_proof():
            logging.error('Logon proof generated by client and server differ. Something is very wrong!')
            return
        else:
            account_flag = byte_buff.get(4)
            logging.info(f'Successfully logged into realm server')
            buff = int.to_bytes(0, 4, 'big')
            packet = connector.Packet(packets.realm.CMD_REALM_LIST, buff)
            return packet

    def handle_CMD_REALM_LIST(self, packet):
        config_realm = self.cfg.get_realm()
        realms = self.parse_realm_list(packet)
        correct_realm = tuple(filter(lambda r: r['name'].lower() == config_realm.lower(), realms))[0]
        if not correct_realm:
            logging.error(f'Realm {config_realm} not found!')
            logging.info('Possible realms:')
            for realm in realms:
                logging.info(realm)
        else:
            logging.debug(f'realm found: {correct_realm}')
            correct_realm['session_key'] = int.to_bytes(self.srp_handler.K, 40, 'little')
            return correct_realm

    def parse_realm_list(self, packet):
        not_vanilla = self.cfg.get_expansion() != 'Vanilla'
        byte_buff = PyByteBuffer.ByteBuffer.wrap(packet.data)
        byte_buff.get(4)
        realms = []
        realm_count = byte_buff.get(2, endianness='little')
        for _ in range(realm_count):
            realm = {}
            realm['is_pvp'] = bool(byte_buff.get(1)) if not_vanilla else None
            realm['lock_flag'] = bool(byte_buff.get(1)) if not_vanilla else None
            realm['flags'] = byte_buff.get(1)  # offline/recommended/for newbies
            realm['name'] = self.read_string(byte_buff)
            address = self.read_string(byte_buff).split(':')
            realm['host'] = address[0]
            realm['port'] = int(address[1])
            realm['population'] = byte_buff.get(4)
            realm['num_chars'] = byte_buff.get(1)
            realm['timezone'] = byte_buff.get(1)
            realm['id'] = byte_buff.get(1)
            if realm['flags'] & 0x04 == 0x04:
                realm['build_info'] = byte_buff.get(5) if not_vanilla else None
                realm['name'] == realm['name'] if not_vanilla else re.sub(r'\(\d+,\d+,\d+\)', '', realm['name'])
            else:
                realm['build_info'] = None
            realms.append(realm)
        return realms

    @staticmethod
    def reset_position(saved_position, buff):
        buff.remaining += buff.position - saved_position
        buff.position = saved_position

    @staticmethod
    def str_to_int(string):
        return int.from_bytes(bytes(string, 'utf-8'), 'big')

    @staticmethod
    def read_string(byte_buff):
        ret = bytearray()
        while byte_buff.remaining:
            byte = byte_buff.get(1)
            if not byte:
                break
            ret += int.to_bytes(byte, 1, 'big')
        return ret.decode('utf-8')
