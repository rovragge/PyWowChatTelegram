import lxml.objectify
import logging


class Config:

    def __init__(self, xmlfile='config.xml'):
        with open(xmlfile, 'r', encoding='utf-8') as file:
            self.xml_obj = lxml.objectify.fromstring(file.read())

    def get_account(self):
        return str(self.xml_obj.wow.account).upper()

    def get_password(self):
        return str(self.xml_obj.wow.password).upper()

    def get_version(self):
        return str(self.xml_obj.wow.version)

    def get_platform(self):
        return str(self.xml_obj.wow.platform)

    def get_realmlist(self):
        return str(self.xml_obj.wow.realmlist)

    def get_locale(self):
        return str(self.xml_obj.wow.locale)

    def get_realm(self):
        return str(self.xml_obj.wow.realm)

    def parse_realm_list(self):
        realm_list = self.get_realmlist()
        split_pos = realm_list.find(':')
        if split_pos == -1:
            host = realm_list
            port = 3724
        else:
            host = realm_list[:split_pos]
            port = realm_list[:split_pos + 1]
        return host, port

    def get_build(self):
        version = self.get_version()
        match version:
            case '1.11.2':
                return 5464
            case '1.12.1':
                return 5875
            case '1.12.2':
                return 6005
            case '1.12.3':
                return 6141
            case '2.4.3':
                return 8606
            case '3.2.2':
                return 10505
            case '3.3.0':
                return 11159
            case '3.3.2':
                return 11723
            case '3.3.5':
                return 12340
            case '4.3.4':
                return 15595
            case '5.4.8':
                return 18414
            case _:
                logging.error(f'Build version {version} not supported')
                raise ValueError

    def get_expansion(self):
        version = self.get_version()
        match version[0]:
            case '1':
                return 'Vanilla'
            case '2':
                return 'TBC'
            case '3':
                return 'WotLK'
            case '4':
                return 'Cataclysm'
            case '5':
                return 'MoP'
            case _:
                logging.error(f'Expansion {version} not supported!')
                raise ValueError
