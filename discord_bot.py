import re

import discord
from discord.ext.commands import Bot
from datetime import datetime

import PyByteBuffer
from src.common.config import glob
from src.common.commonclasses import Packet, ChatMessage


class DiscordBot(Bot):
    FOOTER_URL = 'https://i.kym-cdn.com/photos/images/original/001/475/112/f36.jpg'
    ICC_URL = 'https://static.wikia.nocookie.net/wowpedia/images/f/fc/Icecrown_Citadel_loading_screen.jpg'

    def __init__(self, *args, out_queue=None, **kwargs):
        if not out_queue:
            glob.logger.error('Out queue not specified for discord bot')
            raise RuntimeError
        self.out_queue = out_queue
        self.target_channels = {x: [] for x in glob.maps}
        super().__init__(*args, **kwargs)
        self.emoji_map = {glob.codes.classes.WARRIOR: '<:class_warrior:1028688491799904316>',
                          glob.codes.classes.PALADIN: '<:class_paladin:1028688485122584626>',
                          glob.codes.classes.HUNTER: '<:class_hunter:1028688482320781352>',
                          glob.codes.classes.ROGUE: '<:class_rogue:1028688487567872010>',
                          glob.codes.classes.PRIEST: '<:class_priest:1028688485944664175>',
                          glob.codes.classes.DEATH_KNIGHT: '<:class_dk:1028690432454045726>',
                          glob.codes.classes.SHAMAN: '<:class_shaman:1028688488662564985>',
                          glob.codes.classes.MAGE: '<:class_mage:1028688483776213032>',
                          glob.codes.classes.WARLOCK: '<:class_warlock:1028688490445160498>',
                          glob.codes.classes.DRUID: '<:class_druid:1028690434920300584>'}

    # --------- EVENTS ---------
    async def on_ready(self):
        for guild in self.guilds:
            for channel in guild.channels:
                for x in self.target_channels:
                    if channel.name == glob.maps[x]:
                        self.target_channels[x].append(channel)
        for channel in self.target_channels[glob.codes.chat_channels.SYSTEM]:
            await channel.send('Bot is online')
        glob.logger.info('Discord bot is online')

    async def on_message(self, message):
        if message.author == self.user:
            return
        else:
            if message.channel in glob.maps[glob.codes.chat_channels.GUILD]:
                msg = ChatMessage()
                msg.channel = glob.codes.chat_channels.GUILD
                msg.text = message.content
                msg.language = glob.character.language
                self.send_message_to_wow(msg)

    # --------- HANDLERS ---------

    async def handle_packet(self, packet):
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
            await handler(packet.data)

    async def handle_PURGE_CALENDAR(self, data):
        for guild in self.guilds:
            channel = discord.utils.get(guild.channels, name=glob.maps[glob.codes.chat_channels.ANNOUNCEMENT])
            if channel:
                await channel.purge()

    async def handle_ACTIVITY_UPDATE(self, data):
        activity = discord.Activity(name=f'{data} members online', type=discord.ActivityType.watching)
        await self.change_presence(status=discord.Status.online, activity=activity)

    async def handle_MESSAGE(self, data):
        for guild in self.guilds:
            channel = discord.utils.get(guild.channels, name=glob.maps[data.channel])
            if channel:
                await channel.send(data.text)

    async def handle_REMOVE_CALENDAR_EVENT(self, data):
        await data.delete()

    async def handle_ADD_CALENDAR_EVENT(self, data):
        embed = self.generate_embed(data)
        for guild in self.guilds:
            channel = discord.utils.get(guild.channels, name=glob.maps[glob.codes.chat_channels.ANNOUNCEMENT])
            if channel:
                data.embeds.append(await channel.send(embed=embed))

    async def handle_UPDATE_CALENDAR_EVENT(self, data):
        new_embed = self.generate_embed(data)
        for guild in self.guilds:
            channel = discord.utils.get(guild.channels, name=glob.maps[glob.codes.chat_channels.ANNOUNCEMENT])
            if channel:
                for embed in data.embeds:
                    await embed.edit(embed=new_embed)

    def generate_embed(self, event):
        embed = discord.Embed(title=event.title,
                              colour=discord.Colour.darker_grey(),
                              timestamp=datetime.now(glob.timezone),
                              description=f'`{event.time.strftime("%d/%m/%Y %H:%M")} МСК`')
        # embed.set_image(url=DiscordBot.ICC_URL)
        embed.set_thumbnail(url=DiscordBot.ICC_URL)
        embed.set_footer(text='Generated by PyWowChat\nhttps://github.com/Anarom/PyWowChat',
                         icon_url=DiscordBot.FOOTER_URL)
        embed.add_field(name='Сообщение', value=event.text or 'No text')
        author = glob.players.get(event.invites[0].guid)
        embed.add_field(name='Создатель', value=f'{self.emoji_map[author.char_class]} {author.name}')
        invites = ''
        for invite in event.invites[1:]:
            player = glob.players.get(invite.guid)
            invites += f'{self.emoji_map[player.char_class]} {player.name} {invite.get_status_emoji()}\n\n'
        embed.add_field(name='Подписаны', value=invites[:-2] or 'Empty', inline=False)
        return embed

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
