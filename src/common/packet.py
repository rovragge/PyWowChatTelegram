import PyByteBuffer


class Packet:
    def __init__(self, packet_id, packet_data):
        self.id = packet_id
        self.data = packet_data

    def __str__(self):
        return f'{self.id:04X} - {self.bytes_to_hex_str(self.data, True, False)}'

    def __repr__(self):
        return f'Packet({self.id:04X})'

    def to_byte_buff(self):
        return PyByteBuffer.ByteBuffer.wrap(self.data)

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
