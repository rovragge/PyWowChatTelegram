import logging
import os
import datetime
import sys

from src.common.commonclasses import Character, Guild, ConnectionInfo, Calendar

import lxml.objectify
from importlib import import_module


class Globals:

    def __init__(self):
        with open(os.path.join(os.path.dirname(sys.argv[0]), 'config.xml'), 'r', encoding='utf-8') as xml_file:
            xml_obj = lxml.objectify.fromstring(xml_file.read())

        self.connection_info = ConnectionInfo()
        self.character = Character()
        self.guild = Guild()
        self.calendar = Calendar()
        self.logger = self.setup_log(xml_obj.logger)

        self.connection_info.account = str(xml_obj.wow.account).upper()
        self.connection_info.password = str(xml_obj.wow.password).upper()
        self.connection_info.version = str(xml_obj.wow.version)
        self.connection_info.platform = str(xml_obj.wow.platform)
        self.connection_info.locale = str(xml_obj.wow.locale)
        self.connection_info.realm_name = str(xml_obj.wow.realm)
        self.connection_info.host, self.connection_info.port = self.parse_realm_list(str(xml_obj.wow.realmlist))
        self.connection_info.build = self.connection_info.get_build()
        self.connection_info.expansion = self.connection_info.get_expansion()

        self.character.name = str(xml_obj.wow.character).lower()

        self.server_MOTD_enabled = bool(xml_obj.wow.server_motd_enabled)
        self.realm = None
        self.codes = getattr(import_module(f'src.codes.{self.connection_info.expansion}'), 'Codes')
        self.crypt = getattr(import_module(f'src.header_crypt.{self.connection_info.expansion}'), 'GameHeaderCrypt')()
        self.token = str(xml_obj.discord.token)
        self.maps = {self.codes.chat_channels.get_from_str(x.tag.upper()): x for x in
                     xml_obj.discord.channels.getchildren()}
        self.guild_events = {self.codes.guild_events.get_from_str(e.tag.upper()): bool(e) for e in
                             xml_obj.guild_events.getchildren()}

        self.logger.debug('Config values:\n\t'
                          # f'account = {self.account}\n\t'
                          # f'password = {self.password}\n\t'
                          f'platform = {self.connection_info.platform}\n\t'
                          f'locale = {self.connection_info.locale}\n\t'
                          f'expansion = {self.connection_info.expansion}\n\t'
                          f'version = {self.connection_info.version}\n\t'
                          f'build = {self.connection_info.build}\n\t'
                          f'host = {self.connection_info.host}\n\t'
                          f'port = {self.connection_info.port}\n\t'
                          f'realm = {self.connection_info.realm_name}')

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


glob = Globals()
