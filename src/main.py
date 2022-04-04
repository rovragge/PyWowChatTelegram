import asyncio

import config
import realmconnector
import gameconnector


async def run(cfg):
    host, port = cfg.parse_realm_list()
    print(f'Connecting to {host}:{port}')
    reader, writer = await asyncio.open_connection(host, port)

    realm_connector = realmconnector.RealmConnector(cfg, reader, writer)
    game_connector = gameconnector.GameConnector(cfg, reader, writer)

    realm = await realm_connector.connect()
    writer.close()


if __name__ == '__main__':
    cfg = config.Config()
    asyncio.run(run(cfg))
