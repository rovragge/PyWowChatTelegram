import asyncio

from src.common.config import cfg
from src.connector.logon import LogonConnector
from src.connector.game import GameConnector


async def main():
    cfg.logger.info('Running PyWowChat')
    logon_connector = LogonConnector()
    await logon_connector.run()
    del logon_connector
    game_connector = GameConnector()
    await game_connector.run()


if __name__ == '__main__':
    asyncio.run(main())
