import discord
import asyncio
from src.common.config import glob
from src.discord_bot import DiscordBot
from src.connector.base import Connector


class DiscordConnector(Connector):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = DiscordBot('.', out_queue=self.out_queue, status=discord.Status.online,
                              intents=discord.Intents.all())

    def get_handler(self):
        return None

    async def run(self):
        await asyncio.gather(self.receiver_coro(), self.sender_coro())

    async def receiver_coro(self):
        try:
            await self.bot.start(glob.token)
        except discord.errors.LoginFailure:
            glob.logger.critical('Incorrect discord token')
            raise ValueError

    async def sender_coro(self):
        while not self.bot.is_closed():
            while not self.bot.is_ready():
                await asyncio.sleep(1)
            try:
                packet = await self.in_queue.get()
            except asyncio.exceptions.CancelledError:
                break
            else:
                await self.bot.handle_packet(packet)
