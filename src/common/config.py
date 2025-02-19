import csv
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

        dotenv.load_dotenv('./.env')

        with open(os.path.join(os.path.dirname(sys.argv[0]), 'config.xml'), 'r', encoding='utf-8') as xml_file:
            xml_obj = lxml.objectify.fromstring(xml_file.read())
        self.reset()
        self.logger = self.get_logger(xml_obj.logger)
        self.logon_info = self.get_logon_info(xml_obj)
        self.timezone = datetime.timezone(datetime.timedelta(hours=3), 'Moscow')
        self.reconnect_delay = int(xml_obj.wow.reconnect_delay)
        self.db = str(xml_obj.telegram.db)
        self.token = os.getenv('TG_TOKEN')
        self.chat_id = os.getenv('TG_CHAT')
        self.message_thread_id = os.getenv('TG_THREAD')
        self.server_MOTD_enabled = bool(xml_obj.wow.server_motd_enabled)
        self.codes = Codes()
        self.maps = {self.codes.chat_channels.get_from_str(x.tag.upper()): x for x in
                     xml_obj.telegram.channels.getchildren()}
        self.guild_events = {self.codes.guild_events.get_from_str(e.tag.upper()): bool(e) for e in
                             xml_obj.guild_events.getchildren()}
        self.achievements = self.load_achievements()

        self.logger.debug('Config values:\n\t'
                          f'account = {self.logon_info.account}\n\t'
                          f'password = {self.logon_info.password}\n\t'
                          f'platform = {self.logon_info.platform}\n\t'
                          f'locale = {self.logon_info.locale}\n\t'
                          f'expansion = {self.logon_info.expansion}\n\t'
                          f'version = {self.logon_info.version}\n\t'
                          f'build = {self.logon_info.build}\n\t'
                          f'host = {self.logon_info.address.host}\n\t'
                          f'port = {self.logon_info.address.port}\n\t'
                          f'realm = {self.logon_info.address.name}')

    @staticmethod
    def get_logon_info(xml_obj):
        logon_info = LogonInfo()
        logon_info.account = os.environ.get('WOW_ACC').upper()
        logon_info.password = os.environ.get('WOW_PASS').upper()
        logon_info.address.name = os.environ.get('WOW_REALM')
        logon_info.address.parse(os.environ.get('WOW_LOGON'))
        logon_info.version = str(xml_obj.wow.version)
        logon_info.platform = str(xml_obj.wow.platform)
        logon_info.locale = str(xml_obj.wow.locale)
        return logon_info

    @staticmethod
    def get_logger(logger_cfg):
        logger = logging.getLogger(str(logger_cfg.name) if logger_cfg.name else 'app')
        try:
            log_level = getattr(logging, str(logger_cfg.level).upper())
            logger.setLevel(log_level)
        except ValueError or AttributeError:
            logger.setLevel(logging.DEBUG)
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
            logger.addHandler(handler)
        return logger

    def reset(self):
        self.character = Character(name=os.environ.get('WOW_CHAR'))
        self.guild = Guild()
        self.players = {}
        self.calendar = Calendar()
        self.realm = None
        self.crypt = GameHeaderCrypt()

    def load_achievements(self):
        achievements = {}
        csv_file_path = os.path.join(os.path.dirname(sys.argv[0]), 'achievements.csv')
        try:
            with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if not row:
                        continue
                    achievement_id = int(row[0].strip())
                    russian_name = row[1].strip()
                    achievements[achievement_id] = russian_name
            self.logger.debug(f'Loaded {len(achievements)} achievements from CSV')
        except Exception as e:
            self.logger.error(f'Failed to parse achievements CSV {csv_file_path}: {e}')
        return achievements


glob = Globals()
