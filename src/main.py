import asyncio
import logging

import config
import realmconnector
import gameconnector


async def run():
    cfg = config.Config()

    realm_connector = realmconnector.RealmConnector(cfg)
    realm = await realm_connector.connect()

    game_connector = gameconnector.GameConnector(cfg, realm)
    await game_connector.connect()


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    logging.info('Running PyWowChat')
    asyncio.run(run())
