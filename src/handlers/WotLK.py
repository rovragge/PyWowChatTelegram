import secrets
import hashlib
import datetime

import PyByteBuffer

import src.common.utils as utils

from src.common.config import glob
from src.handlers import TBC
from src.common.commonclasses import ChatMessage, Character, CalendarInvite, CalendarEvent, Holiday, Packet


class GamePacketHandler(TBC.GamePacketHandler):
    ADDON_INFO = b'\x9e\x02\x00\x00x\x9cu\xd2\xc1j\xc30\x0c\xc6q\xef)v\xe9\x9b\xec\xb4\xb4P\xc2\xea\xcb\xe2\x9e\x8bb' \
                 b'\x7fKDl98N\xb7\xf6=\xfa\xbee\xb7\r\x94\xf3OH\xf0G\xaf\xc6\x98&\xf2\xfdN%\\\xde\xfd\xc8\xb8"A\xea' \
                 b'\xb95/\xe9{w2\xff\xbc@H\x97\xd5W\xce\xa2ZC\xa5GY\xc6<op\xad\x11_\x8c\x18,\x0b\'\x9a\xb5!\x96\xc02' \
                 b'\xa8\x0b\xf6\x14!\x81\x8aF9\xf5TOy\xd84\x87\x9f\xaa\xe0\x01\xfd:\xb8\x9c\xe3\xa2\xe0\xd1\xeeG\xd2' \
                 b'\x0b\x1dm\xb7\x96+n:\xc6\xdb<\xea\xb2r\x0c\r\xc9\xa4j+\xcb\x0c\xaf\x1fl+R\x97\xfd\x84\xba\x95\xc7' \
                 b'\x92/Y\x95O\xe2\xa0\x82\xfb-\xaa\xdfs\x9c`Ih\x80\xd6\xdb\xe5\t\xfa\x13\xb8B\x01\xdd\xc41n1\x0b' \
                 b'\xca_{{\x1c>\x9e\xe1\x93\xc8\x8d'

    def parse_auth_challenge(self, data):
        buff = PyByteBuffer.ByteBuffer.allocate(400)
        bin_account = bytes(glob.connection_info.account, 'utf-8')

        data.get(4)
        server_seed = data.get(4, 'big')
        client_seed = int.from_bytes(secrets.token_bytes(4), 'big')
        buff.put(0, 2)
        buff.put(glob.connection_info.build, 4, 'little')
        buff.put(0, 4, 'little')
        buff.put(bin_account)
        buff.put(0, 5)
        buff.put(client_seed)
        buff.put(0, 8)
        buff.put(glob.realm['id'], 4, 'little')
        buff.put(3, 8, 'little')

        md = hashlib.sha1(bin_account)
        md.update(bytearray(4))
        md.update(int.to_bytes(client_seed, 4, 'big'))
        md.update(int.to_bytes(server_seed, 4, 'big'))
        md.update(glob.realm['session_key'])

        buff.put(md.digest())
        buff.put(GamePacketHandler.ADDON_INFO)
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
            glob.logger.error(f'Name not known for guid {guid}')
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

    def handle_achievement_event(self, guid, achievement_id):
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
            self.discord_queue.put_nowait(Packet(glob.codes.discord_headers.REMOVE_CALENDAR_EVENT,embed))
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
        event.time = self.unpack_guid(data)
        event.type = data.get(1)
        event.dungeon_id = data.get(4, 'little')
        event.title = utils.read_string(data)
        event.text = utils.read_string(data)
        data.get(9)  # is_repeatable + CALENDAR_MAX_INVITES + unk_time

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
