import asyncio
import re
import emoji

from telegram import Update
from telegram.error import RetryAfter, TimedOut, NetworkError
from telegram.ext import Application, ContextTypes, filters, MessageHandler, CommandHandler

from src.common.WowData import WowData
from src.common.commonclasses import Packet, ChatMessage
from src.common.config import glob
from src.database import Database


class TelegramBot:
    LINK_PATTERN = re.compile(
        r"\|c(?P<color>[\da-fA-F]{6,8})"  # link color
        r"\|H(?P<type>\w+)"  # link type
        r":(?P<id>\d+).*"  # id and optional part
        r"\|h\[(?P<text>.+)]"  # link text
        r"\|h\|r"  # terminator
    )

    def __init__(self, out_queue):
        self.out_queue = out_queue
        self.chat_id = glob.chat_id
        self.message_thread_id = glob.message_thread_id
        self.db = Database()
        self.application = Application.builder().token(glob.token).build()
        self.setup_handlers()

    def setup_handlers(self):
        # Обработчик текстовых сообщений в группе (исключая команды)
        self.application.add_handler(MessageHandler(
            filters.Chat(chat_id=int(self.chat_id)) & filters.TEXT & ~filters.COMMAND,
            self.handle_tg_group_chat_message
        ))

        # Обработчик команды /start
        self.application.add_handler(CommandHandler("start", self.handle_start))

        # Обработчик команды /online
        self.application.add_handler(CommandHandler("online", self.handle_online))

        # Обработчик команды /setnick <Ник>
        self.application.add_handler(CommandHandler("setnick", self.handle_setnick))

    async def start(self):
        # Инициализируем и запускаем приложение Telegram
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()

    async def handle_tg_group_chat_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_message is None:
            return
        if update.effective_message.message_thread_id != int(self.message_thread_id):
            return

        nickname = (self.db.get_nickname(update.effective_user.id)
                    or update.effective_user.username
                    or update.effective_user.first_name)
        demojized_text = emoji.demojize(update.effective_message.text, language='ru')
        full_message = f'<{nickname}> {demojized_text}'

        parts = []
        max_length = 116
        for line in full_message.splitlines():
            line = line.strip()
            if not line:
                continue  # Пропускаем пустые строки
            while len(line) > max_length:
                parts.append(line[:max_length])
                line = line[max_length:]
            if line:
                parts.append(line)

        glob.logger.info(f"Sending message to WoW in {len(parts)} parts: {full_message}")
        for part in parts:
            msg = ChatMessage()
            msg.channel = glob.codes.chat_channels.GUILD
            msg.text = part
            msg.language = glob.character.language
            packet_data = self.get_wow_chat_message(msg)
            await self.out_queue.put(Packet(glob.codes.client_headers.MESSAGECHAT, packet_data))

    # Обработчик команды /start
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        glob.logger.info(
            f"Handle /start command from {update.effective_user.username or update.effective_user.first_name}")
        message = (
            "Привет! Я бот гильдии и переношу сообщения между WoW и Telegram.\n\n"
            "Доступные команды:\n"
            "📌 /online — кто в игре сейчас\n"
            "📌 /setnick <ник> — установить игровой ник для чата\n\n"
            "Пример: /setnick Рагнарос\n"
            "Если ник не установлен, используется имя из Telegram."
        )
        await update.message.reply_text(message)

    # Обработчик команды /online
    async def handle_online(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        glob.logger.info(
            f"Handle /online command from {update.effective_user.username or update.effective_user.first_name}")
        online_players = glob.guild.get_online_list()  # Получаем список онлайн-игроков
        if online_players:
            online_names = ", ".join(char.name for char in online_players)  # Преобразуем список Character в строку
            response = f"Онлайн сейчас ({len(online_players)} чел.): {online_names}"
        else:
            response = "Никто не в сети 😢"
        await update.message.reply_text(response)

    async def handle_setnick(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        glob.logger.info(
            f"Handle /setnick command from {update.effective_user.username or update.effective_user.first_name}")
        if update.effective_message is None:
            return
        if not context.args:
            await update.message.reply_text("Использование: /setnick <Ник>")
            return

        # Собираем ник из аргументов команды
        new_nick = " ".join(context.args)
        tg_id = update.effective_user.id

        # Сохраняем ник через наш класс NicknameDB
        self.db.save_nickname(tg_id, new_nick)
        await update.message.reply_text(f"Ник для игры установлен: {new_nick}")

    async def handle_packet(self, packet):
        # По аналогии с DiscordBot выбираем имя обработчика на основе кода пакета
        handler_name = f'handle_{glob.codes.telegram_headers.get_str(packet.id)}'
        try:
            handler = getattr(self, handler_name)
        except AttributeError:
            glob.logger.error(f'Unhandled telegram header {packet.id}')
            return
        await handler(packet.data)

    async def handle_MESSAGE(self, data):
        if data.channel == glob.codes.chat_channels.GUILD:
            escaped_author = self.escape_markdown(f"<{data.author.name}>")
            escaped_text = self.parse_links_and_escape_markdown(data.text)
            message_text = f"*{escaped_author}* {escaped_text}"
        elif data.channel == glob.codes.chat_channels.GUILD_ACHIEVEMENT:
            achievement_name = glob.achievements.get(data.achievement_id, "Неизвестно")
            achievement_name_escaped = self.escape_markdown(f"[{achievement_name}]")
            message_text = (
                f"🛡️*{data.author.name}* получил достижение "
                f"[{achievement_name_escaped}]"
                f"({glob.db}?achievement={data.achievement_id})"
            )
        else:
            message_text = None

        if message_text:
            await self.safe_send_message(
                chat_id=self.chat_id,
                message_thread_id=self.message_thread_id,
                text=message_text,
                disable_notification=True,
                parse_mode='MarkdownV2'
            )

    async def handle_ADD_CALENDAR_EVENT(self, data):
        glob.logger.info(f"ADD_CALENDAR_EVENT: {data}")

    async def handle_PURGE_CALENDAR(self, data):
        glob.logger.info(f"PURGE_CALENDAR: {data}")

    async def handle_ACTIVITY_UPDATE(self, data):
        pass

    async def handle_GUILD_EVENT(self, data):
        formatted_text = f"🔔 *{self.escape_markdown(data)}* 🔔"
        await self.safe_send_message(
            chat_id=self.chat_id,
            message_thread_id=self.message_thread_id,
            text=formatted_text,
            disable_notification=True,
            parse_mode='MarkdownV2'
        )

    async def safe_send_message(self, **kwargs):
        try:
            return await self.application.bot.send_message(**kwargs)
        except RetryAfter as e:
            glob.logger.warning(f"Rate limit: sleep {e.retry_after}s")
            await asyncio.sleep(e.retry_after)
            return await self.safe_send_message(**kwargs)
        except (TimedOut, NetworkError) as e:
            glob.logger.error(f"Telegram network error: {e}, message dropped")
            return None
        except Exception as e:
            glob.logger.exception(f"Unexpected error in send_message: {e}")
            return None

    def parse_links_and_escape_markdown(self, text: str) -> str:
        """
        Находит в тексте ссылки по шаблону, экранирует части, не являющиеся ссылками,
        а для найденных ссылок экранирует только видимый текст.
        """
        result = []
        last_index = 0

        # Ищем все вхождения по шаблону ссылки
        for match in re.finditer(self.LINK_PATTERN, text):
            start, end = match.span()
            # Экранируем текст до ссылки
            non_link_text = text[last_index:start]
            result.append(self.escape_markdown(non_link_text))

            # Получаем данные ссылки
            link_text = match.group("text")  # видимый текст ссылки
            link_type = match.group("type")
            if link_type in ('trade', 'enchant'):
                link_type = 'spell'
            obj_id = match.group("id")
            # Экранируем видимый текст ссылки (но НЕ квадратные скобки, которые формируют разметку)
            escaped_link_text = self.escape_markdown(f"[{link_text}]")
            # Формируем Markdown-ссылку – здесь сами символы разметки не экранируются
            link = f"[{escaped_link_text}]({glob.db}?{link_type}={obj_id})"
            result.append(link)

            last_index = end

        # Экранируем остаток текста после последней ссылки
        result.append(self.escape_markdown(text[last_index:]))
        return "".join(result)

    @staticmethod
    def get_wow_chat_message(msg, targets=None):
        buff = WowData.allocate(8192)
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

    @staticmethod
    def escape_markdown(text: str) -> str:
        escape_chars = r'\_*[]()~`>#+-=|{}.!'
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        return text
