import asyncio

import discord
import PyByteBuffer
from discord.ext.commands import Bot
from src.common.config import glob
from src.common.commonclasses import Packet, ChatMessage


class DiscordBot(Bot):
    def __init__(self, *args, out_queue=None, **kwargs):
        if not out_queue:
            glob.logger.error('Out queue not specified for discord bot')
            raise RuntimeError
        self.out_queue = out_queue
        self.target_channels = {x: [] for x in glob.maps}
        super().__init__(*args, **kwargs)

    # --------- EVENTS ---------
    async def on_ready(self):
        for guild in self.guilds:
            for channel in guild.channels:
                for x in self.target_channels:
                    if channel.name == glob.maps[x]:
                        self.target_channels[x].append(channel)
        for channel in self.target_channels[glob.codes.chat_channels.GUILD]:
            await channel.send('Bot is online')
        glob.logger.info('Discord bot is online')

    async def on_message(self, message):
        if message.author == self.user:
            return
        else:
            if message.channel in self.target_channels[glob.codes.chat_channels.GUILD]:
                msg = ChatMessage()
                msg.channel = glob.codes.chat_channels.GUILD
                msg.text = message.content
                msg.language = glob.character.language
                self.send_message_to_wow(msg)

    # --------- HANDLERS ---------

    def handle_packet(self, packet):
        handler_name = f'handle_{glob.codes.discord_headers.get_str(packet.id)}'
        if handler_name == 'Unknown':
            glob.logger.error(f'No header specified for code 0x{packet.id:03x}')
            return
        try:
            handler = getattr(self, handler_name)
        except AttributeError:
            glob.logger.error(f'Unhandled discord header {packet.id}')
            return
        else:
            asyncio.create_task(handler(packet.data), name=handler_name)

    async def handle_ACTIVITY_UPDATE(self, data):
        activity = discord.Activity(name=f'{data} members online', type=discord.ActivityType.watching)
        await self.change_presence(status=discord.Status.online, activity=activity)

    async def handle_MESSAGE(self, msg):
        for channel in self.target_channels[msg.channel]:
            await channel.send(msg.text)

    def send_message_to_wow(self, msg, target=None):
        buff = PyByteBuffer.ByteBuffer.allocate(8192)
        buff.put(msg.channel, 4, 'little')
        buff.put(msg.language, 4, 'little')
        if target:
            buff.put(bytes(target, 'utf-8'))
            buff.put(0)
        buff.put(bytes(msg.text, 'utf-8'))
        buff.put(0)
        buff.strip()
        buff.rewind()
        self.out_queue.put_nowait(Packet(glob.codes.client_headers.MESSAGECHAT, buff.array()))

    async def handle_GUILD_EVENT(self, data):
        for channel in self.target_channels[glob.codes.chat_channels.GUILD]:
            await channel.send(f'```{data}```')
