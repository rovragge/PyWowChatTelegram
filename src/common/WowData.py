import datetime
from PyByteBuffer import ByteBuffer

from src.common.config import glob
from src.common.commonclasses import Realm, Character, ChatMessage, CalendarEvent, CalendarInvite, Holiday


class WowData(ByteBuffer):

    def __init__(self, data):
        super().__init__()
        self.buffer = data
        self.position = 0
        self.remaining = len(data)

    # ---------- Realm ----------
    def get_realms(self):
        self.get(4)
        realms = [self._get_realm() for _ in range(self.get(2, 'little'))]
        string = 'Available realms:' + ''.join(
            [f'\n\t{realm.address.name} {"PvP" if realm.is_pvp else "PvE"} - {realm.address.host}:{realm.address.port}'
             for realm in realms])
        glob.logger.debug(string)
        return realms

    def _get_realm(self):
        realm = Realm()
        realm.is_pvp = bool(self.get(1))
        realm.lock_flag = bool(self.get(1))
        realm.flags = self.get(1)  # offline/recommended/for newbies
        realm.address.name = self.read_string()
        realm.address.parse(self.read_string())
        realm.population = self.get(4)
        realm.num_chars = self.get(1)
        realm.timezone = self.get(1)
        realm.id = self.get(1)
        realm.build_info = self.get(5) if realm.flags & 0x04 == 0x04 else None
        return realm

    # ---------- Chars ----------
    def get_queried_char(self):
        guid = self.unpack_guid()
        name_unknown = self.get(1)
        if name_unknown:
            glob.logger.error(f'Name not known for guid {guid}')
            return None
        char = Character()
        char.guid = guid
        char.name = self.read_string()
        char.cross_name = self.read_string()
        char.race = self.get(1)
        char.gender = self.get(1)
        char.char_class = self.get(1)
        return char

    def get_roster(self):
        n_of_chars = self.get_int()
        roster = {}
        glob.guild.motd = self.read_string()
        glob.guild.info = self.read_string()
        n_of_ranks = self.get_int()
        for _ in range(n_of_ranks):
            rank_info = self.get(8 + 48, 'little')  # TODO split into rank info and guild bank info
        for _ in range(n_of_chars):
            char = self._get_roster_char()
            roster[char.guid] = char
        return roster

    def _get_roster_char(self):
        char = Character()
        char.guid = self.get_big_int()
        is_online = bool(self.get(1))
        char.name = self.read_string()
        char.guild_rank = self.get_int()
        char.level = self.get(1)
        char.char_class = self.get(1)
        self.get(1)  # unknown
        char.position.zone = self.get_int()
        char.last_logoff = 0 if is_online else self.get_int()
        self.read_string()
        self.read_string()
        return char

    def get_account_chars(self):
        chars = [self._get_account_char() for _ in range(self.get(1))]
        glob.logger.debug('Available characters:' + ''.join([f'\n\t{char.name}' for char in chars]))
        return chars

    def _get_account_char(self):
        char = Character()
        char.guid = self.get_big_int()
        char.name = self.read_string()
        char.race = self.get(1)
        char.language = glob.codes.races.get_language(char.race)
        char.char_class = self.get(1)
        char.gender = self.get(1)
        char.appearance.skin = self.get(1)
        char.appearance.face = self.get(1)
        char.appearance.hair_style = self.get(1)
        char.appearance.hair_color = self.get(1)
        char.appearance.facial_hair = self.get(1)
        char.level = self.get(1)
        char.position.zone = self.get_int()
        char.position.map = self.get_int()
        char.position.x = self.get_int()
        char.position.y = self.get_int()
        char.position.z = self.get_int()
        char.guild_guid = self.get_int()
        char.flags = self.get_int()
        self.get(4)  # character customize flags
        self.get(1)  # first login
        char.pet_info = self.get(12, 'little')
        char.equip_info = self.get(19 * 9, 'little')
        char.bag_display_info = self.get(4 * 9, 'little')
        return char

    # ---------- Messages ----------
    def get_chat_message(self):
        msg = ChatMessage()
        msg.channel = self.get(1)
        if msg.channel == glob.codes.chat_channels.GUILD_ACHIEVEMENT:
            # TODO achievement handling
            return
        msg.language = self.get_int()
        if msg.language == 0xFFFFFFFF:  # addon messages
            return
        msg.guid = self.get_big_int()
        if msg.channel != glob.codes.chat_channels.SYSTEM and msg.guid == glob.character.guid:
            return
        self.get(4)
        msg.channel_name = self.read_string() if msg.channel == glob.codes.chat_channels.CHANNEL else None
        # TODO Check if channel is handled or is an achievement message
        self.get_big_int()  # guid
        msg.text = self.read_string(size=self.get_int() - 1)
        self.get(2)  # null terminator + chat tag
        return msg

    def get_motd_messages(self):
        return [self._get_motd_message() for _ in range(self.get_int())]

    def _get_motd_message(self):
        msg = ChatMessage()
        msg.guid = 0
        msg.channel = glob.codes.chat_channels.SYSTEM
        msg.text = self.read_string()
        return msg

    # ---------- Calendar ----------
    def get_calendar_event_ids(self):
        for _ in range(self.get_int()):
            self.get(19)  # event_id(8) + invite_id(8) + status(1) + rank(1) + is_guild_event(1)
            self.unpack_guid()  # creator_guid
        for _ in range(self.get_int()):
            event_id = self.get_big_int()
            self.read_string()  # title
            self.get(16)  # type(4) + time(4) + flags(4) + dungeon_id(4)
            self.unpack_guid()  # creator_guid
            yield event_id

    def get_calendar_event(self):
        event = CalendarEvent()
        self.get(1)
        event.creator_guid = self.unpack_guid()
        event.id = self.get_big_int()
        event.title = self.read_string()
        event.text = self.read_string()
        event.type = self.get(1)
        self.get(1)  # is_repeatable
        self.get_int()  # CALENDAR_MAX_INVITES
        event.dungeon_id = self.get_int()
        if event.dungeon_id == 4294967295:
            event.dungeon_id = -1
        event.flags = self.get_int()
        event.time = self.unpack_time()
        self.get_int()  # unk_time
        event.guild_id = self.get_int()
        event.invites = {}
        for _ in range(self.get_int()):
            invite = self.get_calendar_invite(event.id)
            event.invites[invite.guid] = invite
        return event

    def get_calendar_event_update(self):
        self.get(1)
        event_id = self.get_big_int()
        event = glob.calendar.events.get(event_id)
        if not event:
            glob.logger.error(f'Received update for {event_id}, but no such event recorded')
            return
        self.get_int()  # old_time
        event.flags = self.get_int()
        event.time = self.unpack_time()
        event.type = self.get(1)
        event.dungeon_id = self.get_int()
        event.title = self.read_string()
        event.text = self.read_string()
        self.get(9)  # is_repeatable + CALENDAR_MAX_INVITES + unk_time
        return event

    def get_calendar_invite(self, event_id):
        invite = CalendarInvite()
        invite.guid = self.unpack_guid()
        invite.event_id = event_id
        invite.level = self.get(1)  # level
        invite.status = self.get(1)
        invite.rank = self.get(1)
        self.get(9)  # is_guild_event + 1st item in invite map
        self.get_int()  # last_update_time - has len=14?
        self.read_string()
        return invite

    def get_calendar_holiday(self):
        holiday = Holiday()
        holiday.id = self.get_int()
        holiday.region = self.get_int()
        holiday.looping = self.get_int()
        holiday.priority = self.get_int()
        holiday.filter_type = self.get_int()
        holiday.dates = [self.get_int() for _ in range(Holiday.MAX_HOLIDAY_DATES)]
        holiday.durations = [self.get_int() for _ in range(Holiday.MAX_HOLIDAY_DURATIONS)]
        holiday.flags = [self.get_int() for _ in range(Holiday.MAX_HOLIDAY_FLAGS)]
        holiday.texture_name = self.read_string()
        return holiday

    def get_calendar_direct_invite(self):
        invite = CalendarInvite()
        invite.guid = self.unpack_guid()
        invite.event_id = self.get_big_int()
        invite.id = self.get_big_int()
        invite.level = self.get(1)
        invite.status = self.get(1)
        invite.is_pre = not bool(self.get(1))
        if not invite.is_pre:
            invite.status_time = self.unpack_time()
        invite.is_signup = not bool(self.get(1))
        return invite

    # ---------- Util ----------
    def get_int(self, endianness='little'):
        return self.get(4, endianness)

    def get_big_int(self, endianness='little'):
        return self.get(8, endianness)

    def read_string(self, size=None):
        btarr = bytearray()
        while self.remaining:
            byte = self.get(1)
            if not byte:
                break
            btarr += int.to_bytes(byte, 1, 'big')
            if size and len(btarr) == size:
                break
        return btarr.decode('utf-8', errors='ignore')

    def unpack_guid(self):
        y = self.get(1)
        result = 0
        for x in range(8):
            on_bit = 1 << x
            if (y & on_bit) == on_bit:
                result = result | ((self.get(1) & 0xFF) << (x * 8))
            else:
                result = result
        return result

    def unpack_time(self):
        bin_time = bin(self.get_int())[2:]
        return datetime.datetime(year=2000 + int(bin_time[:5], 2),
                                 month=1 + int(bin_time[5:9], 2),
                                 day=1 + int(bin_time[9:15], 2),
                                 hour=int(bin_time[18:23], 2),
                                 minute=int(bin_time[23:], 2),
                                 tzinfo=glob.timezone)
