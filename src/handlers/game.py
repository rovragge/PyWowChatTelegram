import time
import secrets
import hashlib
import datetime

import PyByteBuffer

from src.common.config import glob

import src.common.utils as utils
from src.common.commonclasses import Packet, ChatMessage, Character, Holiday, CalendarEvent, CalendarInvite
from src.handlers.base import PacketHandler


class GamePacketHandler(PacketHandler):
    ADDON_INFO = b'\x9e\x02\x00\x00x\x9cu\xd2\xc1j\xc30\x0c\xc6q\xef)v\xe9\x9b\xec\xb4\xb4P\xc2\xea\xcb\xe2\x9e\x8bb' \
                 b'\x7fKDl98N\xb7\xf6=\xfa\xbee\xb7\r\x94\xf3OH\xf0G\xaf\xc6\x98&\xf2\xfdN%\\\xde\xfd\xc8\xb8"A\xea' \
                 b'\xb95/\xe9{w2\xff\xbc@H\x97\xd5W\xce\xa2ZC\xa5GY\xc6<op\xad\x11_\x8c\x18,\x0b\'\x9a\xb5!\x96\xc02' \
                 b'\xa8\x0b\xf6\x14!\x81\x8aF9\xf5TOy\xd84\x87\x9f\xaa\xe0\x01\xfd:\xb8\x9c\xe3\xa2\xe0\xd1\xeeG\xd2' \
                 b'\x0b\x1dm\xb7\x96+n:\xc6\xdb<\xea\xb2r\x0c\r\xc9\xa4j+\xcb\x0c\xaf\x1fl+R\x97\xfd\x84\xba\x95\xc7' \
                 b'\x92/Y\x95O\xe2\xa0\x82\xfb-\xaa\xdfs\x9c`Ih\x80\xd6\xdb\xe5\t\xfa\x13\xb8B\x01\xdd\xc41n1\x0b' \
                 b'\xca_{{\x1c>\x9e\xe1\x93\xc8\x8d'

    def __init__(self, discord_queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connect_time = time.time_ns()
        self.discord_queue = discord_queue
        self.received_char_enum = False
        self.in_world = False
        self.last_roster_update = None
        self.pending_players = set()
        self.pending_messages = {}

        # ---------- Login Stuff ----------

    def handle_AUTH_CHALLENGE(self, data):
        challenge = self.parse_auth_challenge(data)
        glob.crypt.initialize(glob.realm.session_key)
        self.out_queue.put_nowait(Packet(glob.codes.client_headers.AUTH_CHALLENGE, challenge))

    @staticmethod
    def parse_auth_challenge(data):
        buff = PyByteBuffer.ByteBuffer.allocate(400)
        bin_account = bytes(glob.logon_info.account, 'utf-8')

        data.get(4)
        server_seed = data.get(4, 'big')
        client_seed = int.from_bytes(secrets.token_bytes(4), 'big')
        buff.put(0, 2)
        buff.put(glob.logon_info.build, 4, 'little')
        buff.put(0, 4, 'little')
        buff.put(bin_account)
        buff.put(0, 5)
        buff.put(client_seed)
        buff.put(0, 8)
        buff.put(glob.realm.id, 4, 'little')
        buff.put(3, 8, 'little')

        md = hashlib.sha1(bin_account)
        md.update(bytearray(4))
        md.update(int.to_bytes(client_seed, 4, 'big'))
        md.update(int.to_bytes(server_seed, 4, 'big'))
        md.update(glob.realm.session_key)

        buff.put(md.digest())
        buff.put(GamePacketHandler.ADDON_INFO)
        buff.strip()
        buff.rewind()
        return buff.array()

    def handle_AUTH_RESPONSE(self, data):
        code = data.get(1)
        if code == glob.codes.game_auth_results.OK:
            glob.logger.info('Successfully connected to game server')
            if not self.received_char_enum:
                self.out_queue.put_nowait(Packet(glob.codes.client_headers.CHAR_ENUM, b''))
        else:
            glob.logger.error(glob.codes.logon_auth_results.get_str(code))
            return

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
            if char.name.lower() == glob.character.name.lower():
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
            if glob.logon_info.expansion == 'WotLK':
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
        return data.get(19 * 9, 'little')

    @staticmethod
    def get_bag_display_info(data):
        return data.get(4 * 9, 'little')

    def handle_LOGIN_VERIFY_WORLD(self, data):
        if self.in_world:
            return
        self.in_world = True
        glob.logger.info('Successfully joined the world')
        self.discord_queue.put_nowait(Packet(glob.codes.discord_headers.PURGE_CALENDAR, None))
        self.out_queue.put_nowait(Packet(glob.codes.client_headers.CALENDAR_GET_CALENDAR, b''))
        if glob.character.guild_guid:
            self.out_queue.put_nowait(
                Packet(glob.codes.client_headers.GUILD_QUERY, int.to_bytes(glob.character.guild_guid, 4, 'little')))
        return 2

    # ---------- Guild Stuff ----------
    def update_roster(self):
        if not self.last_roster_update or time.time() - self.last_roster_update > 10:
            self.last_roster_update = time.time()
            self.out_queue.put_nowait(Packet(glob.codes.client_headers.GUILD_ROSTER, b''))

    def handle_GUILD_ROSTER(self, data):
        glob.guild.roster = self.parse_roster(data)
        self.discord_queue.put_nowait(Packet(glob.codes.discord_headers.ACTIVITY_UPDATE,
                                             len([char for char in glob.guild.roster.values() if
                                                  not char.last_logoff]) - 1))

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
        glob.players[char.guid] = char
        glob.logger.debug(f'Updated info about player {char.name} {char.guid}')
        self.pending_players.remove(char.guid)
        messages = self.pending_messages.get(char.guid)
        if not messages:
            return
        for message in messages:
            message.author = char
            self.discord_queue.put_nowait(Packet(glob.codes.discord_headers.MESSAGE, message))
            glob.logger.info(message)
        del self.pending_messages[char.guid]

    def parse_name_query(self, data):
        guid = self.unpack_guid(data)
        name_unknown = data.get(1)
        char = Character()
        if name_unknown:
            glob.logger.error(f'Name not known for guid {guid}')
            return char
        char.guid = guid
        char.name = utils.read_string(data)
        char.cross_name = utils.read_string(data)
        char.race = data.get(1)
        char.gender = data.get(1)
        char.char_class = data.get(1)
        return char

    def send_NAME_QUERY(self, guid):
        if guid in self.pending_players:
            return
        self.pending_players.add(guid)
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
        if msg:
            self.discord_queue.put_nowait(Packet(glob.codes.discord_headers.GUILD_EVENT, msg))
        self.update_roster()

    @staticmethod
    def generate_guild_event_message(event, messages):
        if event not in glob.guild_events:
            glob.logger.error(f'No such guild event {event}')
            return
        if not list(filter(bool, messages)):
            if event == glob.codes.guild_events.MOTD:
                glob.logger.debug('Empty guild MOTD skipped')
            else:
                glob.logger.error('Empty guild event message')
            return
        if glob.guild_events[event] is False:
            glob.logger.info(f'Guild event disabled')
            return
        if event != glob.codes.guild_events.MOTD and glob.character.name.lower() == messages[0].lower():
            return
        match event:
            case glob.codes.guild_events.SIGNED_ON:
                msg = f'[{messages[0]}] заходит в игру]'
            case glob.codes.guild_events.SIGNED_OFF:
                msg = f'[{messages[0]}] выходит offline'
            case glob.codes.guild_events.JOINED:
                msg = f'{messages[0]}] вступил в гильдию'
            case glob.codes.guild_events.LEFT:
                msg = f'[{messages[0]}] покинул гильдию'
            case glob.codes.guild_events.PROMOTED:
                msg = f'[{messages[0]}] повысил [{messages[1]}] до звания {messages[2]}'
            case glob.codes.guild_events.DEMOTED:
                msg = f'[{messages[0]}] понизил [{messages[1]}] до звания {messages[2]}'
            case glob.codes.guild_events.REMOVED:
                msg = f'[{messages[1]}] исключил [{messages[0]}] из гильдии'
            case glob.codes.guild_events.MOTD:
                msg = f'Сообщение дня гильдии: {messages[0]}'
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
                if message.text.startswith('|c'):
                    message.text = message.text[10:]
                message.text = message.text.replace('|r', '')
                self.discord_queue.put_nowait(Packet(glob.codes.discord_headers.MESSAGE, message))
                glob.logger.info(message)
                return
            author = glob.players.get(message.guid)
            if not author:
                if author in self.pending_messages:
                    self.pending_messages[message.guid].append(message)
                else:
                    self.pending_messages[message.guid] = [message]
                    self.send_NAME_QUERY(message.guid)
            else:
                # send message straight away
                message.author = author
                self.discord_queue.put_nowait(Packet(glob.codes.discord_headers.MESSAGE, message))
                glob.logger.info(message)

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
            del glob.players[guid]
        except KeyError:
            glob.logger.debug(f'Can\'t remove info about player guid {guid} - no such guid recorded')
        else:
            glob.logger.info(f'Info about player {glob.players[guid].name} removed')

    def send_notification(self, message):
        pass

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
        glob.logger.info(
            f'Party operation {operation}{(" on member " + target) if target else ""} resulted in {result}')

    def handle_MOTD(self, data):
        if glob.server_MOTD_enabled:
            messages = self.parse_server_MOTD(data)
            for message in messages:
                pass

    @staticmethod
    def parse_server_MOTD(data):
        n_of_messages = data.get(4, 'little')
        messages = []
        for _ in range(n_of_messages):
            msg = ChatMessage()
            msg.guid = 0
            msg.channel = glob.codes.chat_channels.SYSTEM
            msg.text = utils.read_string(data)
            messages.append(msg)
        return messages

    def handle_TIME_SYNC_REQ(self, data):
        counter = data.get(4, 'little')
        uptime = (time.time_ns() - self.connect_time) // 1000000
        out_data = int.to_bytes(counter, 4, 'little') + int.to_bytes(uptime, 4, 'little')
        self.out_queue.put_nowait(Packet(glob.codes.client_headers.TIME_SYNC_RESP, out_data))

    @staticmethod
    def parse_chat_message(data, gm):
        msg = ChatMessage()
        msg.channel = data.get(1)
        if msg.channel == glob.codes.chat_channels.GUILD_ACHIEVEMENT:
            # TODO achievement handling
            return
        msg.language = data.get(4, 'little')
        if msg.language == -1 or msg.language == 4294967295:  # addon messages and questionable stuff
            return
        msg.guid = data.get(8, 'little')
        if msg.channel != glob.codes.chat_channels.SYSTEM and msg.guid == glob.character.guid:
            return
        data.get(4)
        if gm:
            data.get(4)
            utils.read_string(data)
        msg.channel_name = utils.read_string(data) if msg.channel == glob.codes.chat_channels.CHANNEL else None
        # TODO Check if channel is handled or is an achievement message
        data.get(8, 'little')  # guid
        text_len = data.get(4, 'little') - 1
        msg.text = utils.read_string(data, text_len)
        data.get(2)  # null terminator + chat tag
        return msg

    @staticmethod
    def parse_roster(data):
        n_of_chars = data.get(4, 'little')
        roster = {}
        glob.guild.motd = utils.read_string(data)
        glob.guild.info = utils.read_string(data)
        n_of_ranks = data.get(4, 'little')
        for _ in range(n_of_ranks):
            rank_info = data.get(8 + 48, 'little')  # TODO split into rank info and guild bank info
        for _ in range(n_of_chars):
            char = Character()
            char.guid = data.get(8, 'little')
            is_online = bool(data.get(1))
            char.name = utils.read_string(data)
            char.rank = data.get(4, 'little')
            char.level = data.get(1)
            char.char_class = data.get(1)
            data.get(1)  # unknown
            char.position.zone = data.get(4, 'little')
            char.last_logoff = 0 if is_online else data.get(4, 'little')
            utils.read_string(data)
            utils.read_string(data)
            roster[char.guid] = char
        return roster

    @staticmethod
    def handle_achievement_event(guid, achievement_id):
        if not glob.guild:
            glob.logger.error('Received achievement event, but not in guild')
            return
        player = glob.guild.roster.get(guid)
        if not player:
            glob.logger.error(f'Received achievement event, but no player with guid {guid} in roster')
            return
        # TODO send discord notification (player.name, achievement_id)

    def handle_CALENDAR_SEND_CALENDAR(self, data):
        for _ in range(data.get(4, 'little')):
            data.get(19)  # event_id(8) + invite_id(8) + status(1) + rank(1) + is_guild_event(1)
            self.unpack_guid(data)  # creator_guid
        for _ in range(data.get(4, 'little')):
            event_id = data.get(8, 'little')
            utils.read_string(data)  # title
            data.get(16)  # type(4) + time(4) + flags(4) + dungeon_id(4)
            self.unpack_guid(data)  # creator_guid
            self.out_queue.put_nowait(
                Packet(glob.codes.client_headers.CALENDAR_GET_EVENT, int.to_bytes(event_id, 8, 'little')))
        glob.calendar.time = data.get(4, 'little')
        data.get(4)
        for _ in range(data.get(4, 'little')):
            data.get(20)  # map_id(4) + .difficulty(4) + reset_time(4) + instance_id(8)
        data.get(4, 'little')  # 1135753200 Constant date, unk (28.12.2005 07:00)
        for _ in range(data.get(4, 'little')):
            data.get(12)  # map_id(4) + reset_time(4) + zero(4)
        for _ in range(data.get(4, 'little')):
            holiday = Holiday()
            holiday.id = data.get(4, 'little')
            holiday.region = data.get(4, 'little')
            holiday.looping = data.get(4, 'little')
            holiday.priority = data.get(4, 'little')
            holiday.filter_type = data.get(4, 'little')
            holiday.dates = [data.get(4, 'little') for _ in range(Holiday.MAX_HOLIDAY_DATES)]
            holiday.durations = [data.get(4, 'little') for _ in range(Holiday.MAX_HOLIDAY_DURATIONS)]
            holiday.flags = [data.get(4, 'little') for _ in range(Holiday.MAX_HOLIDAY_FLAGS)]
            holiday.texture_name = utils.read_string(data)
            glob.calendar.holidays.append(holiday)

    def handle_CALENDAR_EVENT_REMOVED_ALERT(self, data):
        data.get(1)
        event_id = data.get(8, 'little')
        self.unpack_time(data)  # time
        if event_id not in glob.calendar.events:
            glob.logger.error(f'Received  removal alert for {event_id} calendar event, but no such event recorded')
            return
        event = glob.calendar.events[event_id]
        for embed in event.embeds:
            self.discord_queue.put_nowait(Packet(glob.codes.discord_headers.REMOVE_CALENDAR_EVENT, embed))
        del glob.calendar.events[event_id]
        glob.logger.debug(f'Removed calendar event {event_id}')

    def handle_CALENDAR_EVENT_UPDATED_ALERT(self, data):
        glob.logger.debug('CALENDAR_EVENT_UPDATED_ALERT')
        data.get(1)
        event_id = data.get(8, 'little')
        event = glob.calendar.events.get(event_id)
        if not event:
            glob.logger.error(f'Received update for {event_id}, but no such event recorded')
            return
        data.get(4, 'little')  # old_time
        event.flags = data.get(4, 'little')
        event.time = self.unpack_time(data)
        event.type = data.get(1)
        event.dungeon_id = data.get(4, 'little')
        event.title = utils.read_string(data)
        event.text = utils.read_string(data)
        data.get(9)  # is_repeatable + CALENDAR_MAX_INVITES + unk_time
        self.discord_queue.put_nowait(Packet(glob.codes.discord_headers.UPDATE_CALENDAR_EVENT, event))

    def handle_CALENDAR_EVENT_INVITE(self):
        glob.logger.error('CALENDAR_EVENT_INVITE - not handled')

    def handle_CALENDAR_EVENT_INVITE_ALERT(self, data):
        event_id = data.get(8, 'little')
        self.out_queue.put_nowait(
            Packet(glob.codes.client_headers.CALENDAR_GET_EVENT, int.to_bytes(event_id, 8, 'little')))

    def handle_CALENDAR_SEND_EVENT(self, data):
        data.get(1)  # send type
        event = CalendarEvent()
        event.creator_guid = self.unpack_guid(data)
        event.id = data.get(8, 'little')
        event.title = utils.read_string(data)
        event.text = utils.read_string(data)
        event.type = data.get(1)
        data.get(1)  # is_repeatable
        data.get(4, 'little')  # CALENDAR_MAX_INVITES
        event.dungeon_id = data.get(4, 'little')
        event.flags = data.get(4, 'little')
        event.time = self.unpack_time(data)
        data.get(4, 'little')  # unk_time
        event.guild_id = data.get(4, 'little')
        for _ in range(data.get(4, 'little')):
            invite = CalendarInvite()
            invite.event_id = event.id
            invite.guid = self.unpack_guid(data)
            self.send_NAME_QUERY(invite.guid)
            data.get(1)  # level
            invite.status = data.get(1)
            invite.rank = data.get(1)
            data.get(9)  # is_guild_event + 1st item in invite map
            data.get(4, 'little')  # last_update_time - has len=14?
            utils.read_string(data)
            event.invites.append(invite)
        glob.calendar.events[event.id] = event
        self.discord_queue.put_nowait(Packet(glob.codes.discord_headers.ADD_CALENDAR_EVENT, event))

    @staticmethod
    def unpack_guid(data):
        y = data.get(1)
        result = 0
        for x in range(8):
            on_bit = 1 << x
            if (y & on_bit) == on_bit:
                result = result | ((data.get(1) & 0xFF) << (x * 8))
            else:
                result = result
        return result

    @staticmethod
    def unpack_time(data):
        bin_time = bin(data.get(4, 'little'))[2:]
        return datetime.datetime(year=2000 + int(bin_time[:5], 2),
                                 month=1 + int(bin_time[5:9], 2),
                                 day=1 + int(bin_time[9:15], 2),
                                 hour=int(bin_time[18:23], 2),
                                 minute=int(bin_time[23:], 2),
                                 tzinfo=glob.timezone)
