import time

from src.common import utils as utils
from src.common.config import cfg
from src.handler import Vanilla
from src.common.commonclasses import Packet, ChatMessage, Character


class PacketHandler(Vanilla.PacketHandler):
    def __init__(self, out_queue):
        super().__init__(out_queue)
        self.connect_time = time.time_ns()

    ADDON_INFO = b'\xd0\x01\x00\x00x\x9cu\xcf;\x0e\xc20\x0c\x80\xe1r\x0f.C\x18P\xa5f\xa1eF&q+\xab\x89S\x19\x87GO\x0f' \
                 b'\x0bbq\xbd~\xd6o\xd9%ZW\x90x=\xd4\xa0T\xf8\xd26\xbb\xfc\xdcw\xcdw\xdc\xcf\x1c\xa8&\x1c\tS\xf4\xc4' \
                 b'\x94a\xb1\x96\x88#\xf1d\x06\x8e%\xdf@\xbb2m\xda\x80/\xb5P`T3y\xf2}\x95\x07\xbem\xac\x94\xa2\x03' \
                 b'\x9eMm\xf9\xbe`\xb0\xb3\xadb\xeeK\x98Q\xb7~\xf1\x10\xa4\x98r\x06\x8a&\x0c\x90\x90\xed{\x83@\xc4~' \
                 b'\xa6\x94\xb6\x98\x18\xc56\xca\xe8\x81aB\xf9\xeb\x07c\xab\x8b\xec'

    @staticmethod
    def get_equip_info(data):
        return data.get(19 * 9, 'little')

    @staticmethod
    def get_bag_display_info(data):
        return data.get(9, 'little')

    def parse_chat_message(self, data, gm):
        msg = ChatMessage()
        msg.channel = data.get(1)
        msg.language = data.get(4, 'little')
        if msg.language in (-1, 4294967295):  # addon messages and questionable stuff
            return
        msg.guid = data.get(8, 'little')
        if msg.channel != cfg.codes.chat_channels.SYSTEM and msg.guid == self.character.guid:
            return
        data.get(4)
        msg.channel_name = utils.read_string(data) if msg.channel == cfg.codes.chat_channels.CHANNEL else None
        data.get(8, 'little')  # guid
        txt_len = data.get(4, 'little') - 1
        msg.text = utils.read_string(data, txt_len)
        return msg

    def parse_roster(self, data):
        n_of_chars = data.get(4, 'little')
        roster = {}
        cfg.guild.motd = utils.read_string(data)
        cfg.guild.info = utils.read_string(data)
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

    def handle_MOTD(self, data):
        if cfg.server_MOTD_enabled:
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
            msg.channel = cfg.codes.chat_channels.SYSTEM
            msg.text = utils.read_string(data)
            messages.append(msg)
        return messages

    def handle_TIME_SYNC_REQ(self, data):
        counter = data.get(4, 'little')
        uptime = (time.time_ns() - self.connect_time) // 1000000
        out_data = int.to_bytes(counter, 4, 'little') + int.to_bytes(uptime, 4, 'little')
        self.out_queue.put_nowait(Packet(cfg.codes.client_headers.TIME_SYNC_RESP, out_data))
