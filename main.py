import asyncio

from src.common.config import glob
from src.connector.logon import LogonConnector
from src.connector.game import GameConnector
from src.connector.disc import DiscordConnector


async def logon_coro(in_queue, out_queue):
    while not in_queue.empty():
        await in_queue.get()
    while not out_queue.empty():
        await out_queue.get()
    connector = LogonConnector(in_queue, out_queue)
    try:
        await out_queue.put(connector.get_initial_packet())
        await connector.run(glob.logon_info.address)
    except asyncio.CancelledError:
        return 0
    except ConnectionAbortedError:
        glob.logger.error('Logon discon')
        return 1
    except ConnectionRefusedError:
        glob.logger.error('Logon refused')
        return 1
    except ConnectionResetError:
        glob.logger.error('Can\'t connect')
        return 1
    except ValueError:
        glob.logger.critical('Bad Logon SRP')
        return 2
    else:
        glob.logger.critical('Logon coro exited without cancellation')
        return 2
    finally:
        connector.writer.close()
        await connector.writer.wait_closed()


async def game_coro(in_queue, out_queue, discord_queue):
    connector = GameConnector(discord_queue, in_queue, out_queue)
    try:
        await connector.run(glob.realm.address)
    except ConnectionAbortedError:
        glob.logger.error('Game discon')
        return 1
    except ConnectionRefusedError:
        glob.logger.error('Game refused')
        return 1
    else:
        connector.writer.close()
        glob.logger.critical('Game coro exited without cancellation')
        return 2
    finally:
        connector.writer.close()
        await connector.writer.wait_closed()
        glob.reset()


async def wow_task(in_queue, out_queue, discord_queue):
    while True:
        logon_task = asyncio.create_task(logon_coro(in_queue, out_queue), name='logon_task')
        match await logon_task:
            case 1:
                await asyncio.sleep(glob.reconnect_delay)
                continue
            case 2:
                raise RuntimeError
        game_task = asyncio.create_task(game_coro(in_queue, out_queue, discord_queue), name='game_task')
        match await game_task:
            case 1:
                await asyncio.sleep(glob.reconnect_delay)
            case 2:
                raise RuntimeError


async def discord_task(in_queue, out_queue):
    connector = DiscordConnector(in_queue, out_queue)
    await connector.run()


async def main():
    glob.logger.info('Running PyWowChat')
    in_queue = asyncio.Queue()
    out_queue = asyncio.Queue()
    discord_queue = asyncio.Queue()
    try:
        await asyncio.gather(wow_task(in_queue, out_queue, discord_queue), discord_task(discord_queue, out_queue))
    except RuntimeError:
        glob.logger.critical('Runtime error')
        exit(-1)


if __name__ == '__main__':
    asyncio.run(main())
