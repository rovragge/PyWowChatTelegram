import secrets
import hashlib

import PyByteBuffer

import src.common.utils as utils

from src.common.config import cfg
from src.handler import TBC
from src.common.dataclasses import ChatMessage, Character


class PacketHandler(TBC.PacketHandler):
    ADDON_INFO = b'\x9e\x02\x00\x00x\x9cu\xd2\xc1j\xc30\x0c\xc6q\xef)v\xe9\x9b\xec\xb4\xb4P\xc2\xea\xcb\xe2\x9e\x8bb' \
                 b'\x7fKDl98N\xb7\xf6=\xfa\xbee\xb7\r\x94\xf3OH\xf0G\xaf\xc6\x98&\xf2\xfdN%\\\xde\xfd\xc8\xb8"A\xea' \
                 b'\xb95/\xe9{w2\xff\xbc@H\x97\xd5W\xce\xa2ZC\xa5GY\xc6<op\xad\x11_\x8c\x18,\x0b\'\x9a\xb5!\x96\xc02' \
                 b'\xa8\x0b\xf6\x14!\x81\x8aF9\xf5TOy\xd84\x87\x9f\xaa\xe0\x01\xfd:\xb8\x9c\xe3\xa2\xe0\xd1\xeeG\xd2' \
                 b'\x0b\x1dm\xb7\x96+n:\xc6\xdb<\xea\xb2r\x0c\r\xc9\xa4j+\xcb\x0c\xaf\x1fl+R\x97\xfd\x84\xba\x95\xc7' \
                 b'\x92/Y\x95O\xe2\xa0\x82\xfb-\xaa\xdfs\x9c`Ih\x80\xd6\xdb\xe5\t\xfa\x13\xb8B\x01\xdd\xc41n1\x0b' \
                 b'\xca_{{\x1c>\x9e\xe1\x93\xc8\x8d'

    def parse_auth_challenge(self, data):
        buff = PyByteBuffer.ByteBuffer.allocate(400)
        bin_account = bytes(cfg.account, 'utf-8')

        data.get(4)
        server_seed = data.get(4, 'big')
        client_seed = int.from_bytes(secrets.token_bytes(4), 'big')
        buff.put(0, 2)
        buff.put(cfg.build, 4, 'little')
        buff.put(0, 4, 'little')
        buff.put(bin_account)
        buff.put(0, 5)
        buff.put(client_seed)
        buff.put(0, 8)
        buff.put(cfg.realm['id'], 4, 'little')
        buff.put(3, 8, 'little')

        md = hashlib.sha1(bin_account)
        md.update(bytearray(4))
        md.update(int.to_bytes(client_seed, 4, 'big'))
        md.update(int.to_bytes(server_seed, 4, 'big'))
        md.update(cfg.realm['session_key'])

        buff.put(md.digest())
        buff.put(PacketHandler.ADDON_INFO)
        buff.strip()
        buff.rewind()
        return buff.array()

    @staticmethod
    def get_bag_display_info(data):
        return data.get(4 * 9, 'little')

    def parse_name_query(self, data):
        guid = self.unpack_guid(data)
        name_unknown = data.get(1)
        char = Character()
        if name_unknown:
            cfg.logger.error(f'Name not known for guid {guid}')
            return char
        char.guid = guid
        char.name = utils.read_string(data)
        char.cross_name = utils.read_string(data)
        char.race = data.get(1)
        char.gender = data.get(1)
        char.char_class = data.get(1)
        return char

    def parse_chat_message(self, data, gm):
        msg = ChatMessage()
        msg.channel = data.get(1)
        msg.language = data.get(4, 'little')
        if msg.language == -1 or msg.language == 4294967295:  # addon messages and questionable stuff
            return
        msg.guid = data.get(8, 'little')
        if msg.channel != cfg.codes.chat_channels.SYSTEM and msg.guid == self.character.guid:
            return
        data.get(4)
        if gm:
            data.get(4)
            utils.read_string(data)
        msg.channel_name = utils.read_string(data) if msg.channel == cfg.codes.chat_channels.CHANNEL else None
        # TODO Check if channel is handled or is an achievement message
        data.get(8, 'little')  # guid
        text_len = data.get(4, 'little') - 1
        msg.text = utils.read_string(data, text_len)
        data.get(2)  # null terminator + chat tag
        if tp == cfg.codes.chat_channels.GUILD_ACHIEVEMENT:
            self.handle_achievement_event(guid, data.get(4, 'little'))
        else:
            msg = ChatMessage(guid, tp, text, channel_name)
            cfg.logger.info(f'Chat message: {msg.text}')
            return msg

    def handle_achievement_event(self, guid, achievement_id):
        if not self.guild:
            cfg.logger.error('Received achievement event, but not in guild')
            return
        player = self.guild.roster.get(guid)
        if not player:
            cfg.logger.error(f'Received achievement event, but no player with guid {guid} in roster')
            return
        # TODO send discord notification (player.name, achievement_id)

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
