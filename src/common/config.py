import logging
import os
import datetime
import sys
import dotenv

from src.common.commonclasses import Character, Guild, LogonInfo, Calendar
from src.header_crypt import GameHeaderCrypt
from src.packet_codes import Codes

import lxml.objectify


class Globals:

    def __init__(self):

        dotenv.load_dotenv('./params.env')

        with open(os.path.join(os.path.dirname(sys.argv[0]), 'config.xml'), 'r', encoding='utf-8') as xml_file:
            xml_obj = lxml.objectify.fromstring(xml_file.read())

        self.logon_info = LogonInfo()
        self.character = Character()
        self.guild = Guild()
        self.players = {}
        self.calendar = Calendar()
        self.realm = None

        self.logger = self.setup_log(xml_obj.logger)
        self.timezone = datetime.timezone(datetime.timedelta(hours=3), 'Moscow')

        self.reconnect_delay = int(xml_obj.wow.reconnect_delay)
        self.logon_info.account = os.environ.get('WOW_ACC').upper()
        self.logon_info.password = os.environ.get('WOW_PASS').upper()
        self.logon_info.realm_name = os.environ.get('WOW_REALM')
        self.character.name = os.environ.get('WOW_CHAR')
        self.token = os.environ.get('DISCORD_TOKEN')
        self.logon_info.version = str(xml_obj.wow.version)
        self.logon_info.platform = str(xml_obj.wow.platform)
        self.logon_info.locale = str(xml_obj.wow.locale)
        self.logon_info.host, self.logon_info.port = self.parse_realm_list(os.environ.get('WOW_LOGON'))
        self.logon_info.build = self.logon_info.get_build()
        self.logon_info.expansion = self.logon_info.get_expansion()
        self.server_MOTD_enabled = bool(xml_obj.wow.server_motd_enabled)

        self.codes = Codes()
        self.crypt = None
        self.reset_crypt()

        self.maps = {self.codes.chat_channels.get_from_str(x.tag.upper()): x for x in
                     xml_obj.discord.channels.getchildren()}
        self.guild_events = {self.codes.guild_events.get_from_str(e.tag.upper()): bool(e) for e in
                             xml_obj.guild_events.getchildren()}

        self.logger.debug('Config values:\n\t'
                          f'account = {self.logon_info.account}\n\t'
                          f'password = {self.logon_info.password}\n\t'
                          f'platform = {self.logon_info.platform}\n\t'
                          f'locale = {self.logon_info.locale}\n\t'
                          f'expansion = {self.logon_info.expansion}\n\t'
                          f'version = {self.logon_info.version}\n\t'
                          f'build = {self.logon_info.build}\n\t'
                          f'host = {self.logon_info.host}\n\t'
                          f'port = {self.logon_info.port}\n\t'
                          f'realm = {self.logon_info.realm_name}')

    @staticmethod
    def setup_log(logger_cfg):
        log = logging.getLogger(str(logger_cfg.name) if logger_cfg.name else 'app')
        try:
            log_level = getattr(logging, str(logger_cfg.level).upper())
            log.setLevel(log_level)
        except ValueError or AttributeError:
            log.setLevel(logging.DEBUG)
        handlers = []
        if logger_cfg.to_file:
            now = datetime.datetime.now()
            filename = f'PyWowChat_{now.date()}_{now.time().hour}-{now.time().minute}-{now.time().second}.log'
            path = os.path.join(os.path.dirname(sys.argv[0]), 'logs', filename)
            handlers.append(logging.FileHandler(path))
        if logger_cfg.to_stdout:
            handlers.append(logging.StreamHandler(sys.stdout))
        log_format = str(logger_cfg.format)
        for handler in handlers:
            handler.setFormatter(logging.Formatter(log_format))
            log.addHandler(handler)
        return log

    @staticmethod
    def parse_realm_list(realmlist):
        split_pos = realmlist.find(':')
        if split_pos == -1:
            host = realmlist
            port = 3724
        else:
            host = realmlist[:split_pos]
            port = realmlist[:split_pos + 1]
        return host, port

    def reset_crypt(self):
        self.crypt = GameHeaderCrypt()


glob = Globals()
