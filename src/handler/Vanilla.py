import time
import secrets
import hashlib
import re

import PyByteBuffer

from src.common.config import cfg
from src.common.packet import Packet
from src.common.message import ChatMessage
import src.common.utils as utils
from src.common.SRP import SRPHandler
from src.common.utils import read_string


class Guild:
    def __init__(self, guid):
        self.guid = guid
        self.name = ''
        self.ranks = []
        self.roster = {}

    def __bool__(self):
        return self.guid is not None


class PacketHandler:
    ADDON_INFO = b'V\x01\x00\x00x\x9cu\xcc\xbd\x0e\xc20\x0c\x04\xe0\xf2\x1e\xbc\x0ca@\x95\xc8B\xc3\x8cL\xe2"\x0b\xc7' \
                 b'\xa9\x8c\xcbO\x9f\x1e\x16$\x06s\xebww\x81iY@\xcbi3g\xa3&\xc7\xbe[\xd5\xc7z\xdf}\x12\xbe\x16\xc0' \
                 b'\x8cq$\xe4\x12I\xa8\xc2\xe4\x95H\n\xc9\xc5=\xd8\xb6z\x06K\xf84\x0f\x15Fsg\xbb8\xccz\xc7\x97\x8b' \
                 b'\xbd\xdc&\xcc\xfe0B\xd6\xe6\xca\x01\xa8\xb8\x90\x80Q\xfc\xb7\xa4Pp\xb8\x12\xf3?&A\xfd\xb57\x90' \
                 b'x19f\x8f'

    def __init__(self, out_queue):
        self.out_queue = out_queue
        self.received_char_enum = False
        self.in_world = False
        self.last_roster_update = None
        self.player_roster = {}
        self.character = None
        self.guild = None

    def handle_packet(self, packet):
        data = packet.to_byte_buff()
        match packet.id:
            case cfg.codes.realm_headers.AUTH_LOGON_CHALLENGE:
                return self.handle_AUTH_LOGON_CHALLENGE(packet)
            case cfg.codes.realm_headers.AUTH_LOGON_PROOF:
                return self.handle_AUTH_LOGON_PROOF(packet)
            case cfg.codes.realm_headers.REALM_LIST:
                return self.handle_REALM_LIST(packet)
            case cfg.codes.server_headers.AUTH_CHALLENGE:
                return self.handle_AUTH_CHALLENGE(data)
            case cfg.codes.server_headers.AUTH_RESPONSE:
                return self.handle_AUTH_RESPONSE(data)
            case cfg.codes.server_headers.NAME_QUERY:
                return self.handle_NAME_QUERY(data)
            case cfg.codes.server_headers.CHAR_ENUM:
                return self.handle_CHAR_ENUM(data)
            case cfg.codes.server_headers.LOGIN_VERIFY_WORLD:
                return self.handle_LOGIN_VERIFY_WORLD(data)
            case cfg.codes.server_headers.GUILD_QUERY:
                return self.handle_GUILD_QUERY(data)
            case cfg.codes.server_headers.GUILD_EVENT:
                return self.handle_GUILD_EVENT(data)
            case cfg.codes.server_headers.GUILD_ROSTER:
                return self.handle_GUILD_ROSTER(data)
            case cfg.codes.server_headers.MESSAGECHAT:
                return self.handle_MESSAGECHAT(data)
            case cfg.codes.server_headers.CHANNEL_NOTIFY:
                return self.handle_CHANNEL_NOTIFY(data)
            case cfg.codes.server_headers.NOTIFICATION:
                return self.handle_NOTIFICATION(data)
            case cfg.codes.server_headers.WHO:
                return self.handle_WHO(data)
            case cfg.codes.server_headers.SERVER_MESSAGE:
                return self.handle_SERVER_MESSAGE(data)
            case cfg.codes.server_headers.INVALIDATE_PLAYER:
                return self.handle_INVALIDATE_PLAYER(data)
            case cfg.codes.server_headers.WARDEN_DATA:
                return self.handle_WARDEN_DATA(data)
            case cfg.codes.server_headers.GROUP_INVITE:
                return self.handle_GROUP_INVITE(data)
            case _:
                pass
                # cfg.logger.error(f'No handling method for this type of packet: {hex(packet.id)}')

    def handle_AUTH_LOGON_CHALLENGE(self, packet):
        byte_buff = PyByteBuffer.ByteBuffer.wrap(packet.data)
        byte_buff.get(1)  # error code
        result = byte_buff.get(1)
        if not cfg.codes.logon_auth_results.is_success(result):
            cfg.logger.error(cfg.codes.logon_auth_results.get_str(result))
            raise ValueError

        B = int.from_bytes(byte_buff.array(32), 'little')
        g_length = byte_buff.get(1)
        g = int.from_bytes(byte_buff.array(g_length), 'little')
        n_length = byte_buff.get(1)
        N = int.from_bytes(byte_buff.array(n_length), 'little')
        salt = int.from_bytes(byte_buff.array(32), 'little')
        byte_buff.array(16)
        security_flag = byte_buff.get(1)

        self.srp_handler = SRPHandler(B, g, N, salt, security_flag)
        self.srp_handler.step1()

        buff = bytearray()
        buff += self.srp_handler.A
        buff += self.srp_handler.M

        md = hashlib.sha1(self.srp_handler.A)
        md.update(self.srp_handler.crc_hash)
        buff += md.digest()

        buff += int.to_bytes(0, 2, 'big')
        packet = Packet(cfg.codes.realm_headers.AUTH_LOGON_PROOF, buff)
        self.out_queue.put_nowait(packet)

    def handle_AUTH_LOGON_PROOF(self, packet):
        byte_buff = PyByteBuffer.ByteBuffer.wrap(packet.data)
        result = byte_buff.get(1)
        if not cfg.codes.logon_auth_results.is_success(result):
            cfg.logger.error(cfg.codes.logon_auth_results.get_str(result))
            return
        proof = byte_buff.array(20)
        if proof != self.srp_handler.generate_hash_logon_proof():
            cfg.logger.error(
                'Logon proof generated by client and server differ. Something is very wrong!')
            return
        else:
            byte_buff.get(4)  # account flag
            cfg.logger.info(f'Successfully logged into realm server')
            packet = Packet(cfg.codes.realm_headers.REALM_LIST, int.to_bytes(0, 4, 'big'))
            self.out_queue.put_nowait(packet)

    def handle_REALM_LIST(self, packet):
        realm_name = cfg.realm_name
        realms = self.parse_realm_list(packet)
        target_realm = tuple(filter(lambda r: r['name'].lower() == realm_name.lower(), realms))[0]
        if not target_realm:
            cfg.logger.error(f'Realm {realm_name} not found!')
            return
        target_realm['session_key'] = int.to_bytes(self.srp_handler.K, 40, 'little')
        cfg.realm = target_realm
        return 1

    @staticmethod
    def parse_realm_list(packet):  # different for Vanilla/TBC+
        not_vanilla = cfg.expansion != 'Vanilla'
        byte_buff = PyByteBuffer.ByteBuffer.wrap(packet.data)
        byte_buff.get(4)
        realms = []
        realm_count = byte_buff.get(2, endianness='little')
        for _ in range(realm_count):
            realm = {}
            realm['is_pvp'] = bool(byte_buff.get(1)) if not_vanilla else None
            realm['lock_flag'] = bool(byte_buff.get(1)) if not_vanilla else None
            realm['flags'] = byte_buff.get(1)  # offline/recommended/for newbies
            realm['name'] = read_string(byte_buff)
            address = read_string(byte_buff).split(':')
            realm['host'] = address[0]
            realm['port'] = int(address[1])
            realm['population'] = byte_buff.get(4)
            realm['num_chars'] = byte_buff.get(1)
            realm['timezone'] = byte_buff.get(1)
            realm['id'] = byte_buff.get(1)
            if realm['flags'] & 0x04 == 0x04:
                realm['build_info'] = byte_buff.get(5) if not_vanilla else None
                # exclude build info from realm name
                realm['name'] == realm['name'] if not_vanilla else re.sub(r'\(\d+,\d+,\d+\)', '', realm['name'])
            else:
                realm['build_info'] = None
            realms.append(realm)
        string = 'Available realms:' + ''.join(
            [f'\n\t{realm["name"]} {"PvP" if realm["is_pvp"] else "PvE"} - {realm["host"]}:{realm["port"]}'
             for realm in realms])
        cfg.logger.debug(string)
        return realms

    def handle_AUTH_CHALLENGE(self, data):
        challenge = self.parse_auth_challenge(data)
        cfg.crypt.initialize(cfg.realm['session_key'])
        self.out_queue.put_nowait(Packet(cfg.codes.client_headers.AUTH_CHALLENGE, challenge))

    def parse_auth_challenge(self, data):
        account_bytes = bytes(cfg.account, 'utf-8')
        client_seed = secrets.token_bytes(4)
        server_seed = int.to_bytes(data.get(4), 4, 'big')
        buff = PyByteBuffer.ByteBuffer.allocate(400)
        buff.put(0)
        buff.put(cfg.build, 4, 'little')
        buff.put(account_bytes)
        buff.put(0)
        buff.put(client_seed)
        md = hashlib.sha1(account_bytes)
        md.update(bytearray(4))
        md.update(client_seed)
        md.update(server_seed)
        md.update(cfg.realm['session_key'])
        buff.put(md.digest())
        buff.put(PacketHandler.ADDON_INFO)
        buff.strip()
        buff.rewind()
        return buff.array()

    def handle_AUTH_RESPONSE(self, data):
        code = data.get(1)
        if code == cfg.codes.game_auth_results.OK:
            cfg.logger.info('Successfully logged into game server')
            if not self.received_char_enum:
                self.out_queue.put_nowait(Packet(cfg.codes.client_headers.CHAR_ENUM, b''))
        else:
            cfg.logger.error(cfg.codes.logon_auth_results.get_str(code))
            return

    def handle_CHAR_ENUM(self, data):
        if self.received_char_enum:
            return
        self.received_char_enum = True
        self.character = self.parse_char_enum(data)
        if not self.character:
            cfg.logger.error(f'Character {cfg.character} not found')
            return
        self.guild = Guild(self.character['guild_guid'])
        cfg.logger.info(f'Logging in with character {self.character["name"]}')
        guid = int.to_bytes(self.character['guid'], 8, 'little')
        self.out_queue.put_nowait(Packet(cfg.codes.client_headers.PLAYER_LOGIN, guid))

    def parse_char_enum(self, data):
        n_of_chars = data.get(1)
        chars = []
        correct_char = None
        for _ in range(n_of_chars):
            char = {}
            char['guid'] = data.get(8, 'little')
            char['name'] = utils.read_string(data)
            if char['name'].lower() == cfg.character:
                correct_char = char
            char['race'] = data.get(1)
            char['language'] = cfg.codes.races.get_language(char['race'])
            char['class'] = data.get(1)
            char['gender'] = data.get(1)
            char['skin'] = data.get(1)
            char['face'] = data.get(1)
            char['hair_style'] = data.get(1)
            char['hair_color'] = data.get(1)
            char['facial hair'] = data.get(1)
            char['level'] = data.get(1)
            char['zone'] = data.get(4, 'little')
            char['map'] = data.get(4, 'little')
            char['x'] = data.get(4, 'little')
            char['y'] = data.get(4, 'little')
            char['z'] = data.get(4, 'little')
            char['guild_guid'] = data.get(4, 'little')
            char['flags'] = data.get(4, 'little')
            char['first_login'] = data.get(1)
            char['pet_info'] = data.get(12, 'little')
            char['equip_info'] = self.get_equip_info(data)
            char['bag_display_info'] = self.get_bag_display_info(data)
            chars.append(char)
        log_message = 'Available characters:' + ''.join([f'\n\t{char["name"]}' for char in chars])
        cfg.logger.debug(log_message)
        return correct_char

    @staticmethod
    def get_equip_info(data):
        return data.get(19 * 5, 'little')

    @staticmethod
    def get_bag_display_info(data):
        return data.get(5, 'little')

    def handle_LOGIN_VERIFY_WORLD(self, data):
        if self.in_world:
            return
        self.in_world = True
        cfg.logger.info('Successfully joined the world')
        if self.guild:
            self.update_roster()
            guid = int.to_bytes(self.guild.guid, 4, 'little')
            self.out_queue.put_nowait(Packet(cfg.codes.client_headers.GUILD_QUERY, guid))
        return 2

    def update_roster(self):
        if not self.last_roster_update or time.time() - self.last_roster_update > 60:
            self.last_roster_update = time.time()
            self.out_queue.put_nowait(Packet(cfg.codes.client_headers.GUILD_ROSTER, b''))

    def handle_NAME_QUERY(self, data):
        name_query_message = self.parse_name_query(data)
        # TODO queued  chat messages

    def parse_name_query(self, data):
        guid = data.get(8, 'little')
        name = utils.read_string(data)
        cross_name = utils.read_string(data)
        race = data.get(4, 'little')
        gender = data.get(4, 'little')
        char_class = int.to_bytes(data.get(4, 'little'), 4, 'little')
        msg = {'guid': guid, 'name': name, 'class': char_class}
        return msg

    def handle_GUILD_QUERY(self, data):
        data.get(4)
        self.guild.name = utils.read_string(data)
        self.guild.ranks = []
        for _ in range(10):
            rank = utils.read_string(data)
            if rank:
                self.guild.ranks.append(rank)

    def handle_GUILD_EVENT(self, data):
        event = data.get(1)
        n_of_strings = data.get(1)
        messages = [utils.read_string(data) for _ in range(n_of_strings)]
        self.handle_guild_event(event, messages)
        self.update_roster()

    @staticmethod
    def handle_guild_event(event, messages):
        if not cfg.guild_events[event]:
            return
        if not list(filter(bool, messages)):
            return
        if event != cfg.codes.guild_events.MOTD and cfg.character.lower() == messages[0].lower():
            return
        match event:
            case cfg.codes.guild_events.SIGNED_ON:
                msg = f'{messages[0]} has come online'
            case cfg.codes.guild_events.SIGNED_OFF:
                msg = f'{messages[0]} has come offline'
            case cfg.codes.guild_events.JOINED:
                msg = f'{messages[0]} has joined the guild'
            case cfg.codes.guild_events.LEFT:
                msg = f'{messages[0]} has left the guild'
            case cfg.codes.guild_events.PROMOTED:
                msg = f'{messages[0]} has promoted {messages[1]} to {messages[2]}'
            case cfg.codes.guild_events.DEMOTED:
                msg = f'{messages[0]} has demoted {messages[1]} to {messages[2]}'
            case cfg.codes.guild_events.REMOVED:
                msg = f'{messages[1]} has kicked {messages[0]} from the guild'
            case cfg.codes.guild_events.MOTD:
                msg = f'Guild Message of the Day: {messages[0]}'

        # TODO Send notification to discord

    def handle_GUILD_ROSTER(self, data):
        self.guild.roster = self.parse_roster(data)
        log_message = 'Guild characters:' + ''.join([f'\n\t{char["name"]}' for char in self.guild.roster.values()])
        cfg.logger.debug(log_message)
        self.update_members_online()

    def parse_roster(self, data):
        members = {}
        n_of_chars = data.get(4, 'little')
        motd = utils.read_string(data)
        guild_info = utils.read_string(data)
        n_of_ranks = data.get(4, 'little')
        for _ in range(n_of_ranks):
            data.get(4)
        for _ in range(n_of_chars):
            member = {}
            member['guid'] = data.get(8, 'little')
            member['is_online'] = bool(data.get(1))
            member['name'] = utils.read_string(data)
            member['rank'] = data.get(4, 'little')
            member['level'] = data.get(1)
            member['class'] = data.get(1)
            member['zone_id'] = data.get(4, 'little')
            member['last_logoff'] = data.get(4, 'little') if not member['is_online'] else 0
            utils.read_string(data)
            utils.read_string(data)
            members[member['guid']] = member
        return members

    def handle_MESSAGECHAT(self, data, gm=False):
        message = self.parse_chat_message(data, gm)
        if message:
            self.send_chat_message(message)

    def parse_chat_message(self, data, gm):
        tp = data.get(1)
        lang = data.get(4, 'little')
        if lang == -1:  # addon messages
            return
        if tp == cfg.codes.chat_channels.CHANNEL:
            channel_name = utils.read_string(data)
            data.get(4)
        else:
            channel_name = None

        # TODO Check if channel is handled

        guid = data.get(8, 'little')
        if tp != cfg.codes.chat_channels.SYSTEM and guid == self.character['guid']:
            return
        match tp:
            case cfg.codes.chat_channels.SAY | cfg.codes.chat_channels.YELL:
                target_guid = data.get(8, 'little')
            case _:
                target_guid = None
        text_len = data.get(4, 'little') - 1
        text = utils.read_string(data, text_len)
        return ChatMessage(guid, tp, text, channel_name)

    @staticmethod
    def handle_CHANNEL_NOTIFY(data):
        tp = data.get(1)
        channel_name = utils.read_string(data)
        match tp:
            case cfg.codes.chat_events.YOU_JOINED_NOTICE:
                cfg.logger.info(f'Joined WOW chat channel {channel_name}')
            case cfg.codes.chat_events.WRONG_PASSWORD_NOTICE:
                cfg.logger.error(f'Incorrect password for channel {channel_name}')
            case cfg.codes.chat_events.MUTED_NOTICE:
                cfg.logger.error(f'You do not have permission to speak in {channel_name}')
            case cfg.codes.chat_events.BANNED_NOTICE:
                cfg.logger.error(f'You are banned from channel {channel_name}')
            case cfg.codes.chat_events.WRONG_FACTION_NOTICE:
                cfg.logger.error(f'Wrong faction for channel {channel_name}')
            case cfg.codes.chat_events.INVALID_NAME_NOTICE:
                cfg.logger.error(f'Invalid channel name')
            case cfg.codes.chat_events.THROTTLED_NOTICE:
                cfg.logger.error(f'Wait to send another message to {channel_name}')
            case cfg.codes.chat_events.NOT_IN_AREA_NOTICE:
                cfg.logger.error(f'Not in the right area for channel {channel_name}')
            case cfg.codes.chat_events.NOT_IN_LFG_NOTICE:
                cfg.logger.error(f'Must be LFG before joining channel {channel_name}')

    @staticmethod
    def handle_NOTIFICATION(data):
        cfg.logger.info(f'Notification: {utils.read_string(data)}')

    def handle_WHO(self, data):
        pass

    def handle_SERVER_MESSAGE(self, data):
        tp = data.get(4, 'little')
        text = utils.read_string(data)
        message = ChatMessage(0, cfg.codes.chat_channels.SYSTEM, None, None)
        match tp:
            case cfg.codes.server_messages.SHUTDOWN_TIME:
                message.text = f'Server shutdown in {text}'
            case cfg.codes.server_messages.RESTART_TIME:
                message.text = f'Server restart in {text}'
            case cfg.codes.server_messages.SHUTDOWN_CANCELLED:
                message.text = f'Server shutdown cancelled'
            case cfg.codes.server_messages.RESTART_CANCELLED:
                message.text = f'Server restart cancelled'
            case _:
                cfg.logger.error(f'Unknown type of server message: {tp} - {text}')
                message.text = text
        self.send_chat_message(message)

    def handle_INVALIDATE_PLAYER(self, data):
        guid = data.get(8, 'little')
        try:
            del self.player_roster[guid]
        except KeyError:
            cfg.logger.debug(f'Can\'t remove guid {guid} from player roster')

    def handle_WARDEN_DATA(self, data):
        pass

    def handle_GROUP_INVITE(self, data):
        pass

    def send_chat_message(self, message):
        pass

    def update_members_online(self):
        # TODO Update Discord status
        pass

    def send_message_to_wow(self, tp, message, target=None):
        buff = PyByteBuffer.ByteBuffer.allocate(8192)
        buff.put(tp)
        buff.put(self.character['language'])
        if target:
            buff.put(bytes(target, 'utf-8'))
            buff.put(0)
        buff.put(bytes(message, 'utf-8'))
        buff.put(0)
        buff.strip()
        buff.rewind()
        self.out_queue.put_nowait(Packet(cfg.codes.client_headers.MESSAGECHAT, buff.array()))

    def send_notification(self, message):
        self.send_message_to_wow(cfg.codes.chat_channels.GUILD, message)
