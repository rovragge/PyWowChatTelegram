import re

import discord
from discord.ext.commands import Bot
from datetime import datetime

import PyByteBuffer
from src.common.config import glob
from src.common.commonclasses import Packet, ChatMessage


class DiscordBot(Bot):
    FOOTER_URL = 'https://i.kym-cdn.com/photos/images/original/001/475/112/f36.jpg'
    LINK_REGEXP = re.compile(r'(\|.+?\|)(Hitem|Hachievement|Hspell|Henchant):(\d*):?(.*?)\|h\[(.+?)]\|h\|r\s?')
    EMOJIS = {glob.codes.classes.WARRIOR: '<:class_warrior:1028688491799904316>',
              glob.codes.classes.PALADIN: '<:class_paladin:1028688485122584626>',
              glob.codes.classes.HUNTER: '<:class_hunter:1028688482320781352>',
              glob.codes.classes.ROGUE: '<:class_rogue:1028688487567872010>',
              glob.codes.classes.PRIEST: '<:class_priest:1028688485944664175>',
              glob.codes.classes.DEATH_KNIGHT: '<:class_dk:1028690432454045726>',
              glob.codes.classes.SHAMAN: '<:class_shaman:1028688488662564985>',
              glob.codes.classes.MAGE: '<:class_mage:1028688483776213032>',
              glob.codes.classes.WARLOCK: '<:class_warlock:1028688490445160498>',
              glob.codes.classes.DRUID: '<:class_druid:1028690434920300584>'}
    THUMBNAILS = {
        -1: 'https://static.wikia.nocookie.net/wowwiki/images/0/0e/Wrath_of_the_Lich_King_Northrend_loading_screen.jpg',
        227: 'https://static.wikia.nocookie.net/wowwiki/images/1/1f/Naxxramas_loading_screen.jpg',
        237: 'https://static.wikia.nocookie.net/wowwiki/images/c/cb/Eye_of_Eternity_loading_screen.jpg',
        238: 'https://static.wikia.nocookie.net/wowwiki/images/d/dd/Obsidian_Sanctum_loading_screen.jpg',
        244: 'https://static.wikia.nocookie.net/wowwiki/images/7/73/Ulduar_loading_screen.jpg',
        248: 'https://static.wikia.nocookie.net/wowwiki/images/5/56/Trial_of_the_Crusader_loading_screen.jpg',
        257: 'https://static.wikia.nocookie.net/wowwiki/images/4/46/Onyxia%27s_Lair_loading_screen.jpg',
        280: 'https://static.wikia.nocookie.net/wowwiki/images/f/fc/Icecrown_Citadel_loading_screen.jpg',
        294: 'https://static.wikia.nocookie.net/wowwiki/images/c/c7/Ruby_Sanctum_loading_screen.jpg'
    }
    STATUS_ICONS = {0: '❓',
                    1: '✅',
                    2: '🚫',
                    3: '✅',
                    4: '🚫',
                    5: '❓',
                    6: '✅',
                    7: '❓',
                    8: '❓',
                    9: '🚫'}

    def __init__(self, *args, out_queue=None, **kwargs):
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
        for channel in self.target_channels[glob.codes.chat_channels.SYSTEM]:
            await channel.send('Bot is online')
        glob.logger.info('Discord bot is online')

    async def on_message(self, message):
        if message.author == self.user:
            return
        else:
            if message.channel.name == glob.maps[glob.codes.chat_channels.GUILD]:
                msg = ChatMessage()
                msg.channel = glob.codes.chat_channels.GUILD
                msg.text = message.content
                msg.language = glob.character.language
                await self.out_queue.put(Packet(glob.codes.client_headers.MESSAGECHAT, self.get_wow_chat_messgage(msg)))

    def get_wow_chat_messgage(self, msg, targets=None):
        buff = PyByteBuffer.ByteBuffer.allocate(8192)
        buff.put(msg.channel, 4, 'little')
        buff.put(msg.language, 4, 'little')
        if targets:
            for target in targets:
                buff.put(bytes(target, 'utf-8'))
                buff.put(0)
        buff.put(bytes(msg.text, 'utf-8'))
        buff.put(0)
        buff.strip()
        buff.rewind()
        return buff.array()

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
                await channel.send(f'[{data.author.name if data.author else "SYSTEM"}]: {self.parse_links(data.text)}')

    @staticmethod
    def parse_links(text):
        result = re.search(DiscordBot.LINK_REGEXP, text)
        if result:
            link = f'{glob.db}?{result[2][1:]}={result[3]}'
            text = re.sub(DiscordBot.LINK_REGEXP, link, text)
        return text

    async def handle_ADD_CALENDAR_EVENT(self, data):
        new_embed = self.generate_embed(data)
        if data.embeds:
            for embed in data.embeds:
                await embed.edit(embed=new_embed)
            return
        for guild in self.guilds:
            channel = discord.utils.get(guild.channels, name=glob.maps[glob.codes.chat_channels.ANNOUNCEMENT])
            if channel:
                embed = await channel.send(embed=new_embed)
                data.embeds.append(embed)

    @staticmethod
    def generate_embed(event):
        embed = discord.Embed(title=event.title,
                              colour=discord.Colour.darker_grey(),
                              timestamp=datetime.now(glob.timezone),
                              description=f'`{event.time.strftime("%d/%m/%Y %H:%M")} МСК`')
        # embed.set_image(url=DiscordBot.ICC_URL)
        image = DiscordBot.THUMBNAILS.get(event.dungeon_id)
        if not image:
            glob.logger.error(f'No thumbnail for dungeon {event.dungeon_id}')
            image = DiscordBot.THUMBNAILS[-1]
        embed.set_image(url=image)
        embed.set_footer(text='Generated by PyWowChat\nhttps://github.com/Anarom/PyWowChat',
                         icon_url=DiscordBot.FOOTER_URL)
        embed.add_field(name='ID', value=f'{event.id}')
        author = glob.players.get(event.creator_guid)
        if author:
            embed.add_field(name='Создатель', value=f'{DiscordBot.EMOJIS[author.char_class]} {author.name}')
        embed.add_field(name='Сообщение', value=event.text or 'Empty', inline=False)

        invites = ''
        for invite in event.invites.values():
            if invite.guid == event.creator_guid:
                continue
            player = glob.players.get(invite.guid)
            if player:
                invites += f'{DiscordBot.EMOJIS.get(player.char_class)} ' \
                           f'{player.name} ' \
                           f'{DiscordBot.STATUS_ICONS.get(invite.status)}\n'
        embed.add_field(name='Подписаны', value=invites[:-1] or 'Empty', inline=True)
        return embed

    async def handle_GUILD_EVENT(self, data):
        for channel in self.target_channels[glob.codes.chat_channels.GUILD]:
            await channel.send(f'`{data}`')
