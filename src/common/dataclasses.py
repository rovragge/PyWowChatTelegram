import PyByteBuffer
from src.common.config import cfg
from src.common.utils import bytes_to_hex_str


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
            return f'[{cfg.codes.chat_channels.get_str(self.channel)}] ' \
                   f'{self.author.name if not self.is_system() else ""}: ' \
                   f'{self.text}'

    def is_system(self):
        return not bool(self.guid)


class Packet:
    def __init__(self, packet_id, packet_data):
        self.id = packet_id
        self.data = packet_data

    def __str__(self):
        return f'{self.id:04X} - {bytes_to_hex_str(self.data)}'

    def __repr__(self):
        return f'Packet({self.id:04X})'

    def to_byte_buff(self):
        return PyByteBuffer.ByteBuffer.wrap(self.data)


class Character:
    def __init__(self):
        self.guid = None
        self.name = None
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
    def __init__(self):
        self.guid = None
        self.name = None
        self.ranks = []
        self.roster = {}
        self.motd = None
        self.info = None

    def __bool__(self):
        return self.guid is not None
