import time

from src.common.config import cfg
from src.common.utils import read_string
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
        match packet.id:
            case cfg.game_packets.SMSG_GM_MESSAGECHAT:
                return self.handle_SMSG_MESSAGECHAT(packet)
            case cfg.game_packets.SMSG_MOTD:
                return self.handle_SMSG_MOTD(packet)
            case cfg.game_packets.SMSG_TIME_SYNC_REQ:
                return self.handle_SMSG_TIME_SYNC_REQ(packet)
            case _:
                return super().handle_packet(packet)

    @staticmethod
    def get_equip_info(buff):
        return buff.get(19 * 9, 'little')

    @staticmethod
    def get_bag_display_info(buff):
        return buff.get(9, 'little')

    def handle_SMSG_MOTD(self, packet):
        if cfg.server_MOTD_enabled:
            messages = self.parse_server_MOTD(packet.to_byte_buff())
            for message in messages:
                self.send_chat_message(message)

    @staticmethod
    def parse_server_MOTD(buff):
        n_of_messages = buff.get(4, 'little')
        messages = []
        for _ in range(n_of_messages):
            message = {'guid': 0, 'tp': cfg.game_packets.CHAT_MSG_SYSTEM, 'text': read_string(buff), 'channel': None}
            messages.append(message)
        return messages

    def parse_chat_message(self, packet):
        raise NotImplementedError

    def parse_guild_roster(self, buff):
        n_of_members = buff.get(4, 'little')
        members = {}
        guild_motd = read_string(buff)
        guild_info = read_string(buff)
        n_of_ranks = buff.get(4, 'little')
        for _ in range(n_of_ranks):
            rank_info = buff.get(8 + 48, 'little')  # TODO split into rank info and guild bank info
        for _ in range(n_of_members):
            member = {}
            member['guid'] = buff.get(8, 'little')
            member['is_online'] = bool(buff.get(1))
            member['name'] = read_string(buff)
            member['rank'] = buff.get(4, 'little')
            member['level'] = buff.get(1)
            member['class'] = buff.get(1)
            buff.get(1)  # unknown
            member['zone_id'] = buff.get(4, 'little')
            member['last_logoff'] = 0 if member['is_online'] else buff.get(4, 'little')  # TODO needs to be float?
            read_string(buff)
            read_string(buff)
            members[member['guid']] = member
        string = 'Guild members:' + ''.join([f'\n\t{m["name"]} Level {m["level"]} '
                                             f'{cfg.game_packets.get_class_str(m["class"])} '
                                             f'{"Online" if m["is_online"] else "Last seen " + m["last_logoff"]}'
                                             for m in members])
        cfg.logger.debug(string)
        return members

    def handle_SMSG_TIME_SYNC_REQ(self, packet):
        counter = packet.to_byte_buff().get(4, 'little')
        uptime = (time.time_ns() - self.connect_time) // 1000000
        data = int.to_bytes(counter, 4, 'little') + int.to_bytes(uptime, 4, 'little')
        self.out_queue.put_nowait(Packet(cfg.game_packets.CMSG_TIME_SYNC_RESP, data))
