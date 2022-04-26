import PyByteBuffer
from src.common.utils import bytes_to_hex_str


class Packet:
    def __init__(self, packet_id, packet_data):
        self.id = packet_id
        self.data = packet_data

    def __str__(self):
        return f'{self.id:04X} - {bytes_to_hex_str(self.data)}'

    def __repr__(self):
        return f'Packet({self.id:04X})'

    def to_byte_buff(self):
        return PyByteBuffer.ByteBuffer.wrap(self.data)
