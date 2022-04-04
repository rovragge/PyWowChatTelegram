import logging


class Packet:
    def __init__(self, packet_id, packet_data):
        self.id = packet_id
        self.data = packet_data

    def __str__(self):
        return f'{self.id:04X} - {self.bytes_to_hex_str(self.data, True, False)}'

    @staticmethod
    def bytes_to_hex_str(data, add_spaces=False, resolve_plain_text=True):
        string = ''
        for byte in data:
            if resolve_plain_text and 0x20 <= byte >= 0x7f:
                string += byte + ' '
            else:
                string += f'{byte:02X}'
            if add_spaces:
                string += ' '
        return string


class Connector:
    def __init__(self, cfg):
        self.cfg = cfg
        self.reader = None
        self.writer = None

    async def send(self, packet, is_realm_packet=False):
        temp_array = bytearray()
        temp_array.append(packet.id)
        self.writer.write(bytes(temp_array) + bytes(packet.data))
        await self.writer.drain()
        logging.debug(f'SEND {"REALM" if is_realm_packet else "GAME"} PACKET: {packet}')

    async def connect(self):
        raise NotImplementedError

    def decode(self, data):
        raise NotImplementedError

    def assign_packet_handler(self, packet):
        raise NotImplementedError
