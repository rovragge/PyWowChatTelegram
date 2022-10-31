import asyncio

from src.common.config import glob
from src.connector.logon import LogonConnector
from src.connector.game import GameConnector
from src.connector.disc import DiscordConnector


async def wow_task(in_queue, out_queue, discord_queue):
    while True:
        connector = LogonConnector(in_queue, out_queue)
        await connector.run()
        connector = GameConnector(discord_queue, in_queue, out_queue)
        await connector.run()
        glob.reset_crypt()
        await asyncio.sleep(glob.reconnect_delay)
        glob.logger.info('Reconnecting to WoW')


async def discord_task(in_queue, out_queue):
    connector = DiscordConnector(in_queue, out_queue)
    await connector.run()


async def main():
    glob.logger.info('Running PyWowChat')
    in_queue = asyncio.Queue()
    out_queue = asyncio.Queue()
    discord_queue = asyncio.Queue()
    await asyncio.gather(wow_task(in_queue, out_queue, discord_queue), discord_task(discord_queue, out_queue))


if __name__ == '__main__':
    asyncio.run(main())
