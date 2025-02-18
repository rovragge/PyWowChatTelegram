from src.common.config import glob


class PacketHandler:
    def __init__(self, out_queue):
        self.out_queue = out_queue

    def handle_packet(self, packet):
        header = glob.codes.server_headers.get_str(packet.id)
        if header != 'Unknown':
            try:
                handler = getattr(self, f'handle_{header}')
            except AttributeError:
                # glob.logger.debug(f'Code specified for {header}, but no handlers method found')
                return
            else:
                return handler(packet.data)
