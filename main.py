import asyncio

from src.common.config import cfg
from src.connector.realm import RealmConnector
from src.connector.game import GameConnector


async def main():
    cfg.logger.info('Running PyWowChat')
    realm_connector = RealmConnector()
    game_connector = GameConnector()
    await realm_connector.run()
    await game_connector.run()


if __name__ == '__main__':
    asyncio.run(main())
