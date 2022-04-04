import asyncio
import logging

import config
import realmconnector
import gameconnector


async def run():
    cfg = config.Config()
    host, port = cfg.parse_realm_list()
    logging.info(f'Connecting to {host}:{port}')
    reader, writer = await asyncio.open_connection(host, port)

    realm_connector = realmconnector.RealmConnector(cfg, reader, writer)
    game_connector = gameconnector.GameConnector(cfg, reader, writer)

    realm = await realm_connector.connect()
    await game_connector.connect(realm)
    writer.close()


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    logging.info('Running PyWowChat')
    asyncio.run(run())
