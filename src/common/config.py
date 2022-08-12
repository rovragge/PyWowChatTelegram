import logging
import os
import datetime
import sys

import lxml.objectify
from importlib import import_module


class _Config:

    def __init__(self):
        with open(os.path.join(os.path.dirname(sys.argv[0]), 'config.xml'), 'r', encoding='utf-8') as xml_file:
            xml_obj = lxml.objectify.fromstring(xml_file.read())
        self.logger = self.setup_log(xml_obj.logger)
        self.account = str(xml_obj.wow.account).upper()
        self.password = str(xml_obj.wow.password).upper()
        self.character = str(xml_obj.wow.character).lower()
        self.version = str(xml_obj.wow.version)
        self.platform = str(xml_obj.wow.platform)
        self.realmlist = str(xml_obj.wow.realmlist)
        self.locale = str(xml_obj.wow.locale)
        self.realm_name = str(xml_obj.wow.realm)
        self.host, self.port = self.parse_realm_list()
        self.build = self.get_build()
        self.expansion = self.get_expansion()
        self.server_MOTD_enabled = bool(xml_obj.wow.server_motd_enabled)
        self.buff_size = int(xml_obj.wow.buff_size)

        self.discord = None
        self.realm = None
        self.codes = getattr(import_module(f'src.codes.{self.expansion}'), 'Codes')
        self.crypt = getattr(import_module(f'src.header_crypt.{self.expansion}'), 'GameHeaderCrypt')()

        self.guild_events = {self.codes.guild_events.SIGNED_ON: bool(xml_obj.guild_events.online),
                             self.codes.guild_events.SIGNED_OFF: bool(xml_obj.guild_events.offline),
                             self.codes.guild_events.JOINED: bool(xml_obj.guild_events.joined),
                             self.codes.guild_events.LEFT: bool(xml_obj.guild_events.left),
                             self.codes.guild_events.REMOVED: bool(xml_obj.guild_events.removed),
                             self.codes.guild_events.PROMOTED: bool(xml_obj.guild_events.promoted),
                             self.codes.guild_events.DEMOTED: bool(xml_obj.guild_events.demoted),
                             self.codes.guild_events.MOTD: bool(xml_obj.guild_events.motd)}
        self.logger.debug('Config values:\n\t'
                          # f'account = {self.account}\n\t'
                          # f'password = {self.password}\n\t'
                          f'platform = {self.platform}\n\t'
                          f'locale = {self.locale}\n\t'
                          f'expansion = {self.expansion}\n\t'
                          f'version = {self.version}\n\t'
                          f'build = {self.build}\n\t'
                          f'host = {self.host}\n\t'
                          f'port = {self.port}\n\t'
                          f'realm = {self.realm_name}')

    @staticmethod
    def setup_log(logger_cfg):
        log = logging.getLogger(str(logger_cfg.name) if logger_cfg.name else 'app')
        match str(logger_cfg.level).lower():
            case 'critical':
                log.setLevel(logging.CRITICAL)
            case 'error':
                log.setLevel(logging.ERROR)
            case 'warning':
                log.setLevel(logging.WARNING)
            case 'info':
                log.setLevel(logging.INFO)
            case 'debug' | _:
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

    def parse_realm_list(self):
        split_pos = self.realmlist.find(':')
        if split_pos == -1:
            host = self.realmlist
            port = 3724
        else:
            host = self.realmlist[:split_pos]
            port = self.realmlist[:split_pos + 1]
        return host, port

    def get_build(self):
        build_map = {'1.11.2': 5464, '1.12.1': 5875, '1.12.2': 6005, '1.12.3': 6141,
                     '2.4.3': 8606,
                     '3.2.2': 10505, '3.3.0': 11159, '3.3.2': 11723, '3.3.5': 12340}
        build = build_map[self.version]
        if not build:
            self.logger.error(f'Build version {self.version} not supported')
            raise ValueError
        return build

    def get_expansion(self):
        expansion_map = {'1': 'Vanilla', '2': 'TBC', '3': 'WotLK'}
        expansion = expansion_map.get(self.version[0])
        if not expansion:
            self.logger.error(f'Expansion {self.version} not supported!')
            raise ValueError
        return expansion


cfg = _Config()
