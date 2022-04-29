import time

from src.common.config import cfg
from src.common.message import ChatMessage
from src.common import utils as utils
from src.common.packet import Packet
from src.handler.game import Vanilla


class GamePacketHandler(Vanilla.GamePacketHandler):
    def __init__(self, out_queue):
        super().__init__(out_queue)
        self.connect_time = time.time_ns()

    ADDON_INFO = b'\xd0\x01\x00\x00x\x9cu\xcf;\x0e\xc20\x0c\x80\xe1r\x0f.C\x18P\xa5f\xa1eF&q+\xab\x89S\x19\x87GO\x0f' \
                 b'\x0bbq\xbd~\xd6o\xd9%ZW\x90x=\xd4\xa0T\xf8\xd26\xbb\xfc\xdcw\xcdw\xdc\xcf\x1c\xa8&\x1c\tS\xf4\xc4' \
                 b'\x94a\xb1\x96\x88#\xf1d\x06\x8e%\xdf@\xbb2m\xda\x80/\xb5P`T3y\xf2}\x95\x07\xbem\xac\x94\xa2\x03' \
                 b'\x9eMm\xf9\xbe`\xb0\xb3\xadb\xeeK\x98Q\xb7~\xf1\x10\xa4\x98r\x06\x8a&\x0c\x90\x90\xed{\x83@\xc4~' \
                 b'\xa6\x94\xb6\x98\x18\xc56\xca\xe8\x81aB\xf9\xeb\x07c\xab\x8b\xec'

    def handle_packet(self, packet):
        data = packet.to_byte_buff()
        match packet.id:
            case cfg.game_packets.SMSG_GM_MESSAGECHAT:
                return self.handle_SMSG_MESSAGECHAT(data, gm=True)
            case cfg.game_packets.SMSG_MOTD:
                return self.handle_SMSG_MOTD(data)
            case cfg.game_packets.SMSG_TIME_SYNC_REQ:
                return self.handle_SMSG_TIME_SYNC_REQ(data)
            case _:
                return super().handle_packet(packet)

    @staticmethod
    def get_equip_info(data):
        return data.get(19 * 9, 'little')

    @staticmethod
    def get_bag_display_info(data):
        return data.get(9, 'little')

    def handle_SMSG_MOTD(self, data):
        if cfg.server_MOTD_enabled:
            messages = self.parse_server_MOTD(data)
            for message in messages:
                self.send_chat_message(message)

    @staticmethod
    def parse_server_MOTD(data):
        n_of_messages = data.get(4, 'little')
        messages = []
        for _ in range(n_of_messages):
            message = ChatMessage(0, cfg.game_packets.CHAT_MSG_SYSTEM, utils.read_string(data), None)
            messages.append(message)
        return messages

    def parse_chat_message(self, data):
        raise NotImplementedError

    def parse_roster(self, data):
        n_of_chars = data.get(4, 'little')
        members = {}
        guild_motd = utils.read_string(data)
        guild_info = utils.read_string(data)
        n_of_ranks = data.get(4, 'little')
        for _ in range(n_of_ranks):
            rank_info = data.get(8 + 48, 'little')  # TODO split into rank info and guild bank info
        for _ in range(n_of_chars):
            member = {}
            member['guid'] = data.get(8, 'little')
            member['is_online'] = bool(data.get(1))
            member['name'] = utils.read_string(data)
            member['rank'] = data.get(4, 'little')
            member['level'] = data.get(1)
            member['class'] = data.get(1)
            data.get(1)  # unknown
            member['zone_id'] = data.get(4, 'little')
            member['last_logoff'] = 0 if member['is_online'] else data.get(4, 'little')
            utils.read_string(data)
            utils.read_string(data)
            members[member['guid']] = member
        return members

    def handle_SMSG_TIME_SYNC_REQ(self, data):
        counter = data.get(4, 'little')
        uptime = (time.time_ns() - self.connect_time) // 1000000
        out_data = int.to_bytes(counter, 4, 'little') + int.to_bytes(uptime, 4, 'little')
        self.out_queue.put_nowait(Packet(cfg.game_packets.CMSG_TIME_SYNC_RESP, out_data))
