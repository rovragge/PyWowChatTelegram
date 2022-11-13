class ChatMessage:
    def __init__(self):
        self.guid = 0
        self.author = Character()
        self.channel = None
        self.language = None
        self.text = None
        self.channel_name = None

    def __str__(self):
        if self.guid and not self.author:
            return 'NPC speech'
        else:
            return f'[{self.channel}] {self.author.name if not self.is_system() else ""}: {self.text}'

    def is_system(self):
        return not bool(self.guid)


class Packet:
    def __init__(self, packet_id, packet_data):
        self.id = packet_id
        self.data = packet_data

    def __str__(self):
        return f'{self.id:04X} - {self._bytes_to_hex_str(self.data)}'

    def __repr__(self):
        return f'Packet({self.id:04X})'

    @staticmethod
    def _bytes_to_hex_str(data, add_spaces=True, resolve_plain_text=False):
        string = ''
        for byte in data:
            if resolve_plain_text and 32 <= byte < 127:
                string += int.to_bytes(byte, 1, 'big').decode('utf-8')
            else:
                string += f'{byte:02X}'
            if add_spaces:
                string += ' '
        return string.strip()


class Character:
    def __init__(self, name=None):
        self.guid = None
        self.name = name
        self.cross_name = None
        self.race = None
        self.language = None
        self.char_class = None
        self.gender = None
        self.level = None
        self.appearance = CharacterAppearance()
        self.position = CharacterPosition()
        self.flags = None
        self.pet_info = None
        self.equip_info = None
        self.bag_display_info = None

        self.last_logoff = None
        self.guild_rank = None
        self.guild_guid = None

    def __bool__(self):
        return self.guid is not None


class CharacterPosition:
    def __init__(self):
        self.zone = None
        self.map = None
        self.x = None
        self.y = None
        self.z = None


class CharacterAppearance:
    def __init__(self):
        self.skin = None
        self.face = None
        self.hair_style = None
        self.hair_color = None
        self.facial_hair = None


class Guild:
    MAX_RANKS = 10

    def __init__(self):
        self.guid = None
        self.name = None
        self.ranks = []
        self.roster = {}
        self.motd = None
        self.info = None

    def __bool__(self):
        return self.guid is not None

    def get_online(self):
        return len([char for char in self.roster.values() if not char.last_logoff]) - 1


class Address:
    def __init__(self):
        self.name = ''
        self.host = None
        self.port = None

    def parse(self, string):
        string = string.split(':')
        if len(string) == 1:
            self.host = string[0]
            self.port = 3724
        else:
            self.host = string[0]
            self.port = string[1]


class LogonInfo:
    def __init__(self):
        self.account = None
        self.password = None
        self.locale = None
        self.platform = None
        self.version = None
        self.address = Address()
        self.expansion = 'WotLK'
        self.build = 12340


class Realm:
    def __init__(self):
        self.is_pvp = False
        self.lock_flag = None
        self.flags = None
        self.address = Address()
        self.population = None
        self.num_chars = None
        self.timezone = None
        self.id = None
        self.build_info = None
        self.session_key = None


class Calendar:

    def __init__(self):
        self.invites = {}
        self.events = {}
        self.persistence_states = {}
        self.resets = {}
        self.holidays = []

    def dump(self):
        self.__init__()


class CalendarInvite:
    def __init__(self):
        self.guid = None
        self.id = None
        self.event_id = None
        self.level = None
        self.status = None
        self.status_time = None
        self.rank = None
        self.last_update_time = None
        self.is_pre = False
        self.is_signup = False

    def get_status_emoji(self):
        status_map = {0: '❓',
                      1: '✅',
                      2: '🚫',
                      3: '✅',
                      4: '🚫',
                      5: '❓',
                      6: '✅',
                      7: '❓',
                      8: '❓',
                      9: '🚫'}
        return status_map.get(self.status) or '❓'

    def __eq__(self, other):
        return all((self.level == other.level,
                    self.status == other.status,
                    self.rank == other.rank))

    def __str__(self):
        return f'CalendarInvite:\n\t{self.guid = }\n\t{self.event_id = }\n\t{self.level = }\n\t{self.status = }\
\n\t{self.rank = }\n\t{self.last_update_time = }'


class CalendarEvent:

    def __init__(self):
        self.id = None
        self.title = None
        self.text = None
        self.type = None
        self.time = None
        self.flags = None
        self.dungeon_id = None
        self.creator_guid = None
        self.invites = {}
        self.embeds = []

    def __eq__(self, other):
        return all((self.title == other.title,
                    self.text == other.text,
                    self.type == other.type,
                    self.time == other.time,
                    self.flags == other.flags,
                    self.dungeon_id == other.dungeon_id,
                    self.invites == other.invites))

    def is_guild_event(self):
        return self.flags == 1024  # TODO needs testing

    def __str__(self):
        return f'CalendarEvent:\n\t{self.id = }\n\t{self.title = }\n\t{self.time = }\n\t{self.flags = }\n\t\
{self.dungeon_id = }\n\t{self.creator_guid = }\n\t{self.text = }\n\t{self.type = }\n\tinvites: {len(self.invites)}'


class Holiday:
    MAX_HOLIDAY_DATES = 26
    MAX_HOLIDAY_DURATIONS = 10
    MAX_HOLIDAY_FLAGS = 10

    def __init(self):
        self.id = None
        self.region = None
        self.looping = None
        self.priority = None
        self.filter_type = None
        self.dates = []
        self.durations = []
        self.flags = []
        self.texture_name = None
