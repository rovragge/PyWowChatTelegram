import asyncio

from src.common.config import glob
from src.connector.logon import LogonConnector
from src.connector.game import GameConnector


async def main():
    glob.logger.info('Running PyWowChat')
    in_queue = asyncio.Queue()
    out_queue = asyncio.Queue()
    discord_queue = asyncio.Queue()
    logon_connector = LogonConnector(in_queue, out_queue)
    await logon_connector.run()
    game_connector = GameConnector(discord_queue, in_queue, out_queue)
    await game_connector.run()


if __name__ == '__main__':
    asyncio.run(main())
