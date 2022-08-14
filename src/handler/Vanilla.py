import time
import secrets
import hashlib
import re

import PyByteBuffer

from src.common.config import glob

import src.common.utils as utils
from src.common.SRP import SRPHandler
from src.common.utils import read_string
from src.common.commonclasses import Packet, ChatMessage, Guild, Character


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
        self.players = {}
        self.messages_awaiting_name_query = {}

    def handle_packet(self, packet):
        header = glob.codes.server_headers.get_str(packet.id)
        if header == 'Unknown':
            glob.logger.debug(f'UNHANDLED PACKET: 0x{packet.id:03x}')
        else:
            try:
                handler = getattr(self, f'handle_{header}')
            except AttributeError:
                # glob.logger.debug(f'Code specified for {header}, but no handler method found')
                return
            else:
                return handler(packet.to_byte_buff())

                # ---------- Login Stuff ----------

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
        target_realm = tuple(filter(lambda r: r['name'].lower() == glob.connection_info.realm_name.lower(), realms))[0]
        if not target_realm:
            glob.logger.error(f'Realm {glob.connection_info.realm_name} not found!')
            return
        target_realm['session_key'] = int.to_bytes(self.srp_handler.K, 40, 'little')
        glob.realm = target_realm
        return 1

    @staticmethod
    def parse_realm_list(data):  # different for Vanilla/TBC+
        not_vanilla = glob.connection_info.expansion != 'Vanilla'
        data.get(4)
        realms = []
        realm_count = data.get(2, endianness='little')
        for _ in range(realm_count):
            realm = {}
            realm['is_pvp'] = bool(data.get(1)) if not_vanilla else None
            realm['lock_flag'] = bool(data.get(1)) if not_vanilla else None
            realm['flags'] = data.get(1)  # offline/recommended/for newbies
            realm['name'] = read_string(data)
            address = read_string(data).split(':')
            realm['host'] = address[0]
            realm['port'] = int(address[1])
            realm['population'] = data.get(4)
            realm['num_chars'] = data.get(1)
            realm['timezone'] = data.get(1)
            realm['id'] = data.get(1)
            if realm['flags'] & 0x04 == 0x04:
                realm['build_info'] = data.get(5) if not_vanilla else None
                # exclude build info from realm name
                realm['name'] == realm['name'] if not_vanilla else re.sub(r'\(\d+,\d+,\d+\)', '', realm['name'])
            else:
                realm['build_info'] = None
            realms.append(realm)
        string = 'Available realms:' + ''.join(
            [f'\n\t{realm["name"]} {"PvP" if realm["is_pvp"] else "PvE"} - {realm["host"]}:{realm["port"]}'
             for realm in realms])
        glob.logger.debug(string)
        return realms

    def handle_AUTH_CHALLENGE(self, data):
        challenge = self.parse_auth_challenge(data)
        glob.crypt.initialize(glob.realm['session_key'])
        self.out_queue.put_nowait(Packet(glob.codes.client_headers.AUTH_CHALLENGE, challenge))

    def parse_auth_challenge(self, data):
        account_bytes = bytes(glob.account, 'utf-8')
        client_seed = secrets.token_bytes(4)
        server_seed = int.to_bytes(data.get(4), 4, 'big')
        buff = PyByteBuffer.ByteBuffer.allocate(400)
        buff.put(0)
        buff.put(glob.connection_info.build, 4, 'little')
        buff.put(account_bytes)
        buff.put(0)
        buff.put(client_seed)
        md = hashlib.sha1(account_bytes)
        md.update(bytearray(4))
        md.update(client_seed)
        md.update(server_seed)
        md.update(glob.realm['session_key'])
        buff.put(md.digest())
        buff.put(PacketHandler.ADDON_INFO)
        buff.strip()
        buff.rewind()
        return buff.array()

    def handle_AUTH_RESPONSE(self, data):
        code = data.get(1)
        if code == glob.codes.game_auth_results.OK:
            glob.logger.info('Successfully logged into game server')
            if not self.received_char_enum:
                self.out_queue.put_nowait(Packet(glob.codes.client_headers.CHAR_ENUM, b''))
        else:
            glob.logger.error(glob.codes.logon_auth_results.get_str(code))
            return

    def handle_WARDEN_DATA(self, data):
        glob.logger.debug('Handling Warden data')

    def handle_CHAR_ENUM(self, data):
        if self.received_char_enum:
            return
        self.received_char_enum = True
        character = self.parse_char_enum(data)
        if not character:
            glob.logger.error(f'Character {glob.character.name} not found')
            raise ValueError
        glob.character = character
        glob.logger.info(f'Logging in with character {glob.character.name}')
        self.out_queue.put_nowait(
            Packet(glob.codes.client_headers.PLAYER_LOGIN, int.to_bytes(glob.character.guid, 8, 'little')))

    def parse_char_enum(self, data):
        n_of_chars = data.get(1)
        chars = []
        correct_char = None
        for _ in range(n_of_chars):
            char = Character()
            char.guid = data.get(8, 'little')
            char.name = utils.read_string(data)
            if char.name.lower() == glob.character.name:
                correct_char = char
            char.race = data.get(1)
            char.language = glob.codes.races.get_language(char.race)
            char.char_class = data.get(1)
            char.gender = data.get(1)
            char.appearance.skin = data.get(1)
            char.appearance.face = data.get(1)
            char.appearance.hair_style = data.get(1)
            char.appearance.hair_color = data.get(1)
            char.appearance.facial_hair = data.get(1)
            char.level = data.get(1)
            char.position.zone = data.get(4, 'little')
            char.position.map = data.get(4, 'little')
            char.position.x = data.get(4, 'little')
            char.position.y = data.get(4, 'little')
            char.position.z = data.get(4, 'little')
            char.guild_guid = data.get(4, 'little')
            char.flags = data.get(4, 'little')
            if glob.connection_info.expansion == 'WotLK':
                data.get(4)  # character customize flags
            data.get(1)  # first login
            char.pet_info = data.get(12, 'little')
            char.equip_info = self.get_equip_info(data)
            char.bag_display_info = self.get_bag_display_info(data)
            chars.append(char)
        log_message = 'Available characters:' + ''.join([f'\n\t{char.name}' for char in chars])
        glob.logger.debug(log_message)
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
        glob.logger.info('Successfully joined the world')
        if glob.character.guild_guid:
            self.out_queue.put_nowait(
                Packet(glob.codes.client_headers.GUILD_QUERY, int.to_bytes(glob.character.guild_guid, 4, 'little')))
        return 2

    # ---------- Guild Stuff ----------
    def update_roster(self):
        if not self.last_roster_update or time.time() - self.last_roster_update > 60:
            self.last_roster_update = time.time()
            self.out_queue.put_nowait(Packet(glob.codes.client_headers.GUILD_ROSTER, b''))

    def handle_GUILD_ROSTER(self, data):
        glob.guild.roster = self.parse_roster(data)

    def parse_roster(self, data):
        roster = {}
        n_of_chars = data.get(4, 'little')
        glob.guild.motd = utils.read_string(data)
        glob.guild.info = utils.read_string(data)
        n_of_ranks = data.get(4, 'little')
        for _ in range(n_of_ranks):
            data.get(4)
        for _ in range(n_of_chars):
            char = Character()
            char.guid = data.get(8, 'little')
            is_online = bool(data.get(1))
            char.name = utils.read_string(data)
            char.guild_rank = data.get(4, 'little')
            char.level = data.get(1)
            char.char_class = data.get(1)
            char.zone = data.get(4, 'little')
            char.last_logoff = 0 if is_online else data.get(4, 'little')
            utils.read_string(data)
            utils.read_string(data)
            roster[char.guid] = char
        return roster

    def handle_GUILD_QUERY(self, data):
        data.get(4)
        glob.guild.name = utils.read_string(data)
        glob.guild.ranks = []
        for _ in range(10):
            rank = utils.read_string(data)
            if rank:
                glob.guild.ranks.append(rank)

    def handle_NAME_QUERY(self, data):
        char = self.parse_name_query(data)
        self.players[char.guid] = char
        glob.logger.info(f'Updated info about player {char.name}')
        messages = self.messages_awaiting_name_query.get(char.guid)
        if not messages:
            return
        for message in messages:
            message.author = char
            glob.logger.info(message)
            # send messages to discord
        del self.messages_awaiting_name_query[char.guid]

    def parse_name_query(self, data):
        char = Character()
        char.guid = data.get(8, 'little')
        char.name = utils.read_string(data)
        char.cross_name = utils.read_string(data)
        char.race = data.get(4, 'little')
        char.gender = data.get(4, 'little')
        char.char_class = int.to_bytes(data.get(4, 'little'), 4, 'little')
        return char

    def send_NAME_QUERY(self, guid):
        data = PyByteBuffer.ByteBuffer.allocate(8)
        data.put(guid, 8, endianness='little')
        data.rewind()
        self.out_queue.put_nowait(Packet(glob.codes.client_headers.NAME_QUERY, data.array()))

    # ---------- Guild Events ----------
    def handle_GUILD_EVENT(self, data):
        event = data.get(1)
        n_of_strings = data.get(1)
        messages = [utils.read_string(data) for _ in range(n_of_strings)]
        msg = self.generate_guild_event_message(event, messages)
        self.discord_queue.put_nowait(Packet(glob.codes.discord_headers.GUILD_EVENT, msg))
        self.update_roster()

    @staticmethod
    def generate_guild_event_message(event, messages):
        if event not in glob.guild_events:
            glob.logger.error(f'No such guild event {event}')
            return
        if not list(filter(bool, messages)) and event != glob.codes.guild_events.MOTD:
            glob.logger.error('Empty guild event message')
            return
        if glob.guild_events[event] is False:
            glob.logger.info(f'Guild event disabled')
            return
        if event != glob.codes.guild_events.MOTD and glob.character.lower() == messages[0].lower():
            return
        match event:
            case glob.codes.guild_events.SIGNED_ON:
                msg = f'{messages[0]} has come online'
            case glob.codes.guild_events.SIGNED_OFF:
                msg = f'{messages[0]} has come offline'
            case glob.codes.guild_events.JOINED:
                msg = f'{messages[0]} has joined the guild'
            case glob.codes.guild_events.LEFT:
                msg = f'{messages[0]} has left the guild'
            case glob.codes.guild_events.PROMOTED:
                msg = f'{messages[0]} has promoted {messages[1]} to {messages[2]}'
            case glob.codes.guild_events.DEMOTED:
                msg = f'{messages[0]} has demoted {messages[1]} to {messages[2]}'
            case glob.codes.guild_events.REMOVED:
                msg = f'{messages[1]} has kicked {messages[0]} from the guild'
            case glob.codes.guild_events.MOTD:
                msg = f'Guild Message of the Day: {messages[0]}'
            case _:
                glob.logger.error(f'Unknown guild event of type {event}')
                return
        glob.logger.info(f'GUILD EVENT {msg}')
        return msg

    # ---------- Chat Stuff ----------

    def handle_MESSAGECHAT(self, data, gm=False):
        message = self.parse_chat_message(data, gm)
        if not message:
            return
        if glob.maps.get(message.channel):
            if message.channel == glob.codes.chat_channels.SYSTEM:
                # send message straight away
                glob.logger.info(message)
                return
            author = self.players.get(message.guid)
            if not author:
                if author in self.messages_awaiting_name_query:
                    self.messages_awaiting_name_query[message.guid].append(message)
                else:
                    self.messages_awaiting_name_query[message.guid] = [message]
                    self.send_NAME_QUERY(message.guid)
            else:
                # send message straight away
                message.author = author
                glob.logger.info(message)

    def parse_chat_message(self, data, gm):
        raise NotImplementedError

    @staticmethod
    def handle_CHANNEL_NOTIFY(data):
        tp = data.get(1)
        channel_name = utils.read_string(data)
        match tp:
            case glob.codes.chat_events.YOU_JOINED:
                glob.logger.info(f'Joined WOW chat channel {channel_name}')
            case glob.codes.chat_events.WRONG_PASSWORD:
                glob.logger.error(f'Incorrect password for channel {channel_name}')
            case glob.codes.chat_events.MUTED:
                glob.logger.error(f'You do not have permission to speak in {channel_name}')
            case glob.codes.chat_events.BANNED:
                glob.logger.error(f'You are banned from channel {channel_name}')
            case glob.codes.chat_events.WRONG_FACTION:
                glob.logger.error(f'Wrong faction for channel {channel_name}')
            case glob.codes.chat_events.INVALID_NAME:
                glob.logger.error(f'Invalid channel name')
            case glob.codes.chat_events.THROTTLED:
                glob.logger.error(f'Wait to send another message to {channel_name}')
            case glob.codes.chat_events.NOT_IN_AREA:
                glob.logger.error(f'Not in the right area for channel {channel_name}')
            case glob.codes.chat_events.NOT_IN_LFG:
                glob.logger.error(f'Must be LFG before joining channel {channel_name}')

    @staticmethod
    def handle_NOTIFICATION(data):
        glob.logger.info(f'Notification: {utils.read_string(data)}')

    def handle_SERVER_MESSAGE(self, data):
        tp = data.get(4, 'little')
        text = utils.read_string(data)
        msg = ChatMessage()
        msg.channel = glob.codes.chat_channels.SYSTEM
        match tp:
            case glob.codes.server_messages.SHUTDOWN_TIME:
                msg.text = f'Server shutdown in {text}'
            case glob.codes.server_messages.RESTART_TIME:
                msg.text = f'Server restart in {text}'
            case glob.codes.server_messages.SHUTDOWN_CANCELLED:
                msg.text = f'Server shutdown cancelled'
            case glob.codes.server_messages.RESTART_CANCELLED:
                msg.text = f'Server restart cancelled'
            case _:
                glob.logger.error(f'Unknown type of server message: {tp} - {text}')
                msg.text = text
        glob.logger.info(msg)

    def handle_INVALIDATE_PLAYER(self, data):
        guid = data.get(8, 'little')
        try:
            glob.logger.info(f'Info about player {self.players[guid].name} removed')
            del self.players[guid]
        except KeyError:
            glob.logger.debug(f'Can\'t remove info about player guid {guid} - no such guid recorded')

    def send_message_to_wow(self, msg, target=None):
        buff = PyByteBuffer.ByteBuffer.allocate(8192)
        buff.put(msg.channel, 4, 'little')
        buff.put(glob.character['language'], 4, 'little')
        if target:
            buff.put(bytes(target, 'utf-8'))
            buff.put(0)
        buff.put(bytes(msg.text, 'utf-8'))
        buff.put(0)
        buff.strip()
        buff.rewind()
        self.out_queue.put_nowait(Packet(glob.codes.client_headers.MESSAGECHAT, buff.array()))

    def send_notification(self, message):
        self.send_message_to_wow(glob.codes.chat_channels.GUILD, message)

    # ---------- Group ----------
    def handle_GROUP_INVITE(self, data):
        flag = data.get(1)
        name = utils.read_string(data)
        valid_names = ('Ovid', 'Hermes')
        if name in valid_names:
            glob.logger.info(f'Received group invite from {name}. Accepting')
            self.out_queue.put_nowait(Packet(glob.codes.client_headers.GROUP_ACCEPT, bytearray(4)))
        else:
            glob.logger.info(f'Received group invite from {name}. Declining')
            self.out_queue.put_nowait(Packet(glob.codes.client_headers.GROUP_DECLINE, b''))

    def handle_GROUP_SET_LEADER(self, data):
        new_leader = utils.read_string(data)
        glob.logger.info(f'{new_leader} is the new leader')
        if new_leader == glob.character.name:
            self.out_queue.put_nowait(Packet(glob.codes.client_headers.GROUP_RAID_CONVERT, b''))
            self.out_queue.put_nowait(Packet(glob.codes.client_headers.GROUP_DISBAND, b''))

    def send_GROUP_SET_LEADER(self):
        pass

    def handle_GROUP_DESTROYED(self, data):
        glob.logger.info('Party has been disbanded!')

    def handle_PARTY_COMMAND_RESULT(self, data):
        operation = data.get(4, 'little')
        target = utils.read_string(data)
        result = data.get(4, 'little')
        lfg_related = data.get(4)
        glob.logger.info(f'Party operation {operation}{(" on member " + target) if target else ""} resulted in {result}')
