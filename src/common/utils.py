def read_string(buff, size=None):
    btarr = bytearray()
    while buff.remaining:
        byte = buff.get(1)
        if not byte:
            break
        btarr += int.to_bytes(byte, 1, 'big')
        if size and len(btarr) == size:
            break
    return btarr.decode('utf-8')


def bytes_to_hex_str(data, add_spaces=True, resolve_plain_text=False):
    string = ''
    for byte in data:
        if resolve_plain_text and 32 <= byte < 127:
            string += int.to_bytes(byte, 1, 'big').decode('utf-8')
        else:
            string += f'{byte:02X}'
        if add_spaces:
            string += ' '
    return string.strip()
