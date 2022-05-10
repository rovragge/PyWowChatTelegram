import time
import secrets
import hashlib

import PyByteBuffer

from src.common.config import cfg
from src.common.packet import Packet
from src.common.message import ChatMessage
import src.common.utils as utils


class Guild:
    def __init__(self, guid):
        self.guid = guid
        self.name = ''
        self.ranks = []
        self.roster = {}

    def __bool__(self):
        return self.guid is not None


class GamePacketHandler:
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
            case cfg.game_packets.SMSG_AUTH_CHALLENGE:
                return self.handle_SMSG_AUTH_CHALLENGE(data)
            case cfg.game_packets.SMSG_AUTH_RESPONSE:
                return self.handle_SMSG_AUTH_RESPONSE(data)
            case cfg.game_packets.SMSG_NAME_QUERY:
                return self.handle_SMSG_NAME_QUERY(data)
            case cfg.game_packets.SMSG_CHAR_ENUM:
                return self.handle_SMSG_CHAR_ENUM(data)
            case cfg.game_packets.SMSG_LOGIN_VERIFY_WORLD:
                return self.handle_SMSG_LOGIN_VERIFY_WORLD(data)
            case cfg.game_packets.SMSG_GUILD_QUERY:
                return self.handle_SMSG_GUILD_QUERY(data)
            case cfg.game_packets.SMSG_GUILD_EVENT:
                return self.handle_SMSG_GUILD_EVENT(data)
            case cfg.game_packets.SMSG_GUILD_ROSTER:
                return self.handle_SMSG_GUILD_ROSTER(data)
            case cfg.game_packets.SMSG_MESSAGECHAT:
                return self.handle_SMSG_MESSAGECHAT(data)
            case cfg.game_packets.SMSG_CHANNEL_NOTIFY:
                return self.handle_SMSG_CHANNEL_NOTIFY(data)
            case cfg.game_packets.SMSG_NOTIFICATION:
                return self.handle_SMSG_NOTIFICATION(data)
            case cfg.game_packets.SMSG_WHO:
                return self.handle_SMSG_WHO(data)
            case cfg.game_packets.SMSG_SERVER_MESSAGE:
                return self.handle_SMSG_SERVER_MESSAGE(data)
            case cfg.game_packets.SMSG_INVALIDATE_PLAYER:
                return self.handle_SMSG_INVALIDATE_PLAYER(data)
            case cfg.game_packets.SMSG_WARDEN_DATA:
                return self.handle_SMSG_WARDEN_DATA(data)
            case cfg.game_packets.SMSG_GROUP_INVITE:
                return self.handle_SMSG_GROUP_INVITE(data)
            case _:
                pass
                # cfg.logger.error(f'No handling method for this type of packet: {hex(packet.id)}')

    def handle_SMSG_AUTH_CHALLENGE(self, data):
        challenge = self.parse_auth_challenge(data)
        cfg.crypt.initialize(cfg.realm['session_key'])
        self.out_queue.put_nowait(Packet(cfg.game_packets.CMSG_AUTH_CHALLENGE, challenge))

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
        buff.put(GamePacketHandler.ADDON_INFO)
        buff.strip()
        buff.rewind()
        return buff.array()

    def handle_SMSG_AUTH_RESPONSE(self, data):
        code = data.get(1)
        if code == cfg.game_packets.AUTH_OK:
            cfg.logger.info('Successfully logged into game server')
            if not self.received_char_enum:
                self.out_queue.put_nowait(Packet(cfg.game_packets.CMSG_CHAR_ENUM, b''))
        else:
            cfg.logger.error(cfg.auth_results.get_message(code))
            return

    def handle_SMSG_CHAR_ENUM(self, data):
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
        self.out_queue.put_nowait(Packet(cfg.game_packets.CMSG_PLAYER_LOGIN, guid))

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
            char['language'] = cfg.game_packets.get_language(char['race'])
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

    def handle_SMSG_LOGIN_VERIFY_WORLD(self, data):
        if self.in_world:
            return
        self.in_world = True
        cfg.logger.info('Successfully joined the world')
        if self.guild:
            self.update_roster()
            guid = int.to_bytes(self.guild.guid, 4, 'little')
            self.out_queue.put_nowait(Packet(cfg.game_packets.CMSG_GUILD_QUERY, guid))
        return 2

    def update_roster(self):
        if not self.last_roster_update or time.time() - self.last_roster_update > 60:
            self.last_roster_update = time.time()
            self.out_queue.put_nowait(Packet(cfg.game_packets.CMSG_GUILD_ROSTER, b''))

    def handle_SMSG_NAME_QUERY(self, data):
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

    def handle_SMSG_GUILD_QUERY(self, data):
        data.get(4)
        self.guild.name = utils.read_string(data)
        self.guild.ranks = []
        for _ in range(10):
            rank = utils.read_string(data)
            if rank:
                self.guild.ranks.append(rank)

    def handle_SMSG_GUILD_EVENT(self, data):
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
        if event != cfg.game_packets.GE_MOTD and cfg.character.lower() == messages[0].lower():
            return
        match event:
            case cfg.game_packets.GE_SIGNED_ON:
                msg = f'{messages[0]} has come online'
            case cfg.game_packets.GE_SIGNED_OFF:
                msg = f'{messages[0]} has come offline'
            case cfg.game_packets.GE_JOINED:
                msg = f'{messages[0]} has joined the guild'
            case cfg.game_packets.GE_LEFT:
                msg = f'{messages[0]} has left the guild'
            case cfg.game_packets.GE_PROMOTED:
                msg = f'{messages[0]} has promoted {messages[1]} to {messages[2]}'
            case cfg.game_packets.GE_DEMOTED:
                msg = f'{messages[0]} has demoted {messages[1]} to {messages[2]}'
            case cfg.game_packets.GE_REMOVED:
                msg = f'{messages[1]} has kicked {messages[0]} from the guild'
            case cfg.game_packets.GE_MOTD:
                msg = f'Guild Message of the Day: {messages[0]}'

        # TODO Send notification to discord

    def handle_SMSG_GUILD_ROSTER(self, data):
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

    def handle_SMSG_MESSAGECHAT(self, data, gm=False):
        message = self.parse_chat_message(data, gm)
        if message:
            self.send_chat_message(message)

    def parse_chat_message(self, data, gm):
        tp = data.get(1)
        lang = data.get(4, 'little')
        if lang == -1:  # addon messages
            return
        if tp == cfg.game_packets.CHAT_MSG_CHANNEL:
            channel_name = utils.read_string(data)
            data.get(4)
        else:
            channel_name = None

        # TODO Check if channel is handled

        guid = data.get(8, 'little')
        if tp != cfg.game_packets.CHAT_MSG_SYSTEM and guid == self.character['guid']:
            return
        match tp:
            case cfg.game_packets.CHAT_MSG_SAY | cfg.game_packets.CHAT_MSG_YELL:
                target_guid = data.get(8, 'little')
            case _:
                target_guid = None
        text_len = data.get(4, 'little') - 1
        text = utils.read_string(data, text_len)
        return ChatMessage(guid, tp, text, channel_name)

    @staticmethod
    def handle_SMSG_CHANNEL_NOTIFY(data):
        tp = data.get(1)
        channel_name = utils.read_string(data)
        match tp:
            case cfg.game_packets.CHAT_YOU_JOINED_NOTICE:
                cfg.logger.info(f'Joined WOW chat channel {channel_name}')
            case cfg.game_packets.CHAT_WRONG_PASSWORD_NOTICE:
                cfg.logger.error(f'Incorrect password for channel {channel_name}')
            case cfg.game_packets.CHAT_MUTED_NOTICE:
                cfg.logger.error(f'You do not have permission to speak in {channel_name}')
            case cfg.game_packets.CHAT_BANNED_NOTICE:
                cfg.logger.error(f'You are banned from channel {channel_name}')
            case cfg.game_packets.CHAT_WRONG_FACTION_NOTICE:
                cfg.logger.error(f'Wrong faction for channel {channel_name}')
            case cfg.game_packets.CHAT_INVALID_NAME_NOTICE:
                cfg.logger.error(f'Invalid channel name')
            case cfg.game_packets.CHAT_THROTTLED_NOTICE:
                cfg.logger.error(f'Wait to send another message to {channel_name}')
            case cfg.game_packets.CHAT_NOT_IN_AREA_NOTICE:
                cfg.logger.error(f'Not in the right area for channel {channel_name}')
            case cfg.game_packets.CHAT_NOT_IN_LFG_NOTICE:
                cfg.logger.error(f'Must be LFG before joining channel {channel_name}')

    @staticmethod
    def handle_SMSG_NOTIFICATION(data):
        cfg.logger.info(f'Notification: {utils.read_string(data)}')

    def handle_SMSG_WHO(self, data):
        pass

    def handle_SMSG_SERVER_MESSAGE(self, data):
        tp = data.get(4, 'little')
        text = utils.read_string(data)
        message = ChatMessage(0, cfg.game_packets.CHAT_MSG_SYSTEM, None, None)
        match tp:
            case cfg.game_packets.SERVER_MSG_SHUTDOWN_TIME:
                message.text = f'Server shutdown in {text}'
            case cfg.game_packets.SERVER_MSG_RESTART_TIME:
                message.text = f'Server restart in {text}'
            case cfg.game_packets.SERVER_MSG_SHUTDOWN_CANCELLED:
                message.text = f'Server shutdown cancelled'
            case cfg.game_packets.SERVER_MSG_RESTART_CANCELLED:
                message.text = f'Server restart cancelled'
            case _:
                cfg.logger.error(f'Unknown type of server message: {tp} - {text}')
                message.text = text
        self.send_chat_message(message)

    def handle_SMSG_INVALIDATE_PLAYER(self, data):
        guid = data.get(8, 'little')
        try:
            del self.player_roster[guid]
        except KeyError:
            cfg.logger.debug(f'Can\'t remove guid {guid} from player roster')

    def handle_SMSG_WARDEN_DATA(self, data):
        pass

    def handle_SMSG_GROUP_INVITE(self, data):
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
        self.out_queue.put_nowait(Packet(cfg.game_packets.CMSG_MESSAGECHAT, buff.array()))

    def send_notification(self, message):
        self.send_message_to_wow(cfg.game_packets.CHAT_MSG_GUILD, message)
