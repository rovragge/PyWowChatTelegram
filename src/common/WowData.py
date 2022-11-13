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
        n_of_chars = self.get(4, 'little')
        roster = {}
        glob.guild.motd = self.read_string()
        glob.guild.info = self.read_string()
        n_of_ranks = self.get(4, 'little')
        for _ in range(n_of_ranks):
            rank_info = self.get(8 + 48, 'little')  # TODO split into rank info and guild bank info
        for _ in range(n_of_chars):
            char = self._get_roster_char()
            roster[char.guid] = char
        return roster

    def _get_roster_char(self):
        char = Character()
        char.guid = self.get(8, 'little')
        is_online = bool(self.get(1))
        char.name = self.read_string()
        char.guild_rank = self.get(4, 'little')
        char.level = self.get(1)
        char.char_class = self.get(1)
        self.get(1)  # unknown
        char.position.zone = self.get(4, 'little')
        char.last_logoff = 0 if is_online else self.get(4, 'little')
        self.read_string()
        self.read_string()
        return char

    def get_account_chars(self):
        chars = [self._get_account_char() for _ in range(self.get(1))]
        glob.logger.debug('Available characters:' + ''.join([f'\n\t{char.name}' for char in chars]))
        return chars

    def _get_account_char(self):
        char = Character()
        char.guid = self.get(8, 'little')
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
        char.position.zone = self.get(4, 'little')
        char.position.map = self.get(4, 'little')
        char.position.x = self.get(4, 'little')
        char.position.y = self.get(4, 'little')
        char.position.z = self.get(4, 'little')
        char.guild_guid = self.get(4, 'little')
        char.flags = self.get(4, 'little')
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
        msg.language = self.get(4, 'little')
        if msg.language == -1:  # addon messages
            return
        msg.guid = self.get(8, 'little')
        if msg.channel != glob.codes.chat_channels.SYSTEM and msg.guid == glob.character.guid:
            return
        self.get(4)
        msg.channel_name = self.read_string() if msg.channel == glob.codes.chat_channels.CHANNEL else None
        # TODO Check if channel is handled or is an achievement message
        self.get(8, 'little')  # guid
        msg.text = self.read_string(size=self.get(4, 'little') - 1)
        self.get(2)  # null terminator + chat tag
        return msg

    def get_motd_messages(self):
        return [self._get_motd_message() for _ in range(self.get(4, 'little'))]

    def _get_motd_message(self):
        msg = ChatMessage()
        msg.guid = 0
        msg.channel = glob.codes.chat_channels.SYSTEM
        msg.text = self.read_string()
        return msg

    # ---------- Calendar ----------
    def get_calendar_event_ids(self):
        for _ in range(self.get(4, 'little')):
            self.get(19)  # event_id(8) + invite_id(8) + status(1) + rank(1) + is_guild_event(1)
            self.unpack_guid()  # creator_guid
        for _ in range(self.get(4, 'little')):
            event_id = self.get(8, 'little')
            self.read_string()  # title
            self.get(16)  # type(4) + time(4) + flags(4) + dungeon_id(4)
            self.unpack_guid()  # creator_guid
            yield event_id

    def get_calendar_event(self):
        event = CalendarEvent()
        self.get(1)
        event.creator_guid = self.unpack_guid()
        event.id = self.get(8, 'little')
        event.title = self.read_string()
        event.text = self.read_string()
        event.type = self.get(1)
        self.get(1)  # is_repeatable
        self.get(4, 'little')  # CALENDAR_MAX_INVITES
        event.dungeon_id = self.get(4, 'little')
        event.flags = self.get(4, 'little')
        event.time = self.unpack_time()
        self.get(4, 'little')  # unk_time
        event.guild_id = self.get(4, 'little')
        event.invites = {}
        for _ in range(self.get(4, 'little')):
            invite = self.get_calendar_invite(event.id)
            event.invites[invite.guid] = invite
        return event

    def get_calendar_event_update(self):
        self.get(1)
        event_id = self.get(8, 'little')
        event = glob.calendar.events.get(event_id)
        if not event:
            glob.logger.error(f'Received update for {event_id}, but no such event recorded')
            return
        self.get(4, 'little')  # old_time
        event.flags = self.get(4, 'little')
        event.time = self.unpack_time()
        event.type = self.get(1)
        event.dungeon_id = self.get(4, 'little')
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
        self.get(4, 'little')  # last_update_time - has len=14?
        self.read_string()
        return invite

    def get_calendar_holiday(self):
        holiday = Holiday()
        holiday.id = self.get(4, 'little')
        holiday.region = self.get(4, 'little')
        holiday.looping = self.get(4, 'little')
        holiday.priority = self.get(4, 'little')
        holiday.filter_type = self.get(4, 'little')
        holiday.dates = [self.get(4, 'little') for _ in range(Holiday.MAX_HOLIDAY_DATES)]
        holiday.durations = [self.get(4, 'little') for _ in range(Holiday.MAX_HOLIDAY_DURATIONS)]
        holiday.flags = [self.get(4, 'little') for _ in range(Holiday.MAX_HOLIDAY_FLAGS)]
        holiday.texture_name = self.read_string()
        return holiday

    def get_calendar_direct_invite(self):
        invite = CalendarInvite()
        invite.guid = self.unpack_guid()
        invite.event_id = self.get(8, 'little')
        invite.id = self.get(8, 'little')
        invite.level = self.get(1)
        invite.status = self.get(1)
        invite.is_pre = not bool(self.get(1))
        if not invite.is_pre:
            invite.status_time = self.unpack_time()
        invite.is_signup = not bool(self.get(1))
        return invite

    # ---------- Util ----------
    def read_string(self, size=None):
        btarr = bytearray()
        while self.remaining:
            byte = self.get(1)
            if not byte:
                break
            btarr += int.to_bytes(byte, 1, 'big')
            if size and len(btarr) == size:
                break
        return btarr.decode('utf-8')

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
        bin_time = bin(self.get(4, 'little'))[2:]
        return datetime.datetime(year=2000 + int(bin_time[:5], 2),
                                 month=1 + int(bin_time[5:9], 2),
                                 day=1 + int(bin_time[9:15], 2),
                                 hour=int(bin_time[18:23], 2),
                                 minute=int(bin_time[23:], 2),
                                 tzinfo=glob.timezone)
