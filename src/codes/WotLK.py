import src.codes.TBC as TBC


class ServerHeaders(TBC.ServerHeaders):
    GM_MESSAGECHAT = 0x03B3


class ClientHeaders(TBC.ClientHeaders):
    KEEP_ALIVE = 0x0407


class Codes(TBC.Codes):
    server_headers = ServerHeaders
    client_headers = ClientHeaders
