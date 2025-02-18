import re

from telegram import Update
from telegram.ext import Application, ContextTypes, filters, MessageHandler, CommandHandler

from src.common.WowData import WowData
from src.common.commonclasses import Packet, ChatMessage
from src.common.config import glob
from src.database import Database


class TelegramBot:
    LINK_PATTERN = re.compile(
        r"\|c(?P<color>[0-9a-fA-F]{6,8})"  # Цвет ссылки
        r"\|H(?P<type>\w+):"  # Тип ссылки
        r"(?P<id>\d+)"  # ID объекта
        r"(?::[0-9A-Fa-f:-]*)?"  # Необязательная часть с шестнадцатеричными значениями
        r"\|h\[(?P<text>[^\]]+)\]"  # Отображаемый текст ссылки
        r"\|h\|r"  # Завершающая часть
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

        nickname = self.db.get_nickname(update.effective_user.id) or update.effective_user.username or update.effective_user.first_name
        full_message = f'<{nickname}> {update.effective_message.text}'

        max_length = 116
        # Разбиваем полное сообщение на части длиной max_length символов
        parts = [full_message[i:i + max_length] for i in range(0, len(full_message), max_length)]

        for part in parts:
            msg = ChatMessage()
            msg.channel = glob.codes.chat_channels.GUILD
            msg.text = part
            msg.language = glob.character.language
            packet_data = self.get_wow_chat_message(msg)
            await self.out_queue.put(Packet(glob.codes.client_headers.MESSAGECHAT, packet_data))

    # Обработчик команды /start
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        glob.logger.info(f"Handle /start command from {update.effective_user.username or update.effective_user.first_name}")
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
        glob.logger.info(f"Handle /online command from {update.effective_user.username or update.effective_user.first_name}")
        online_players = glob.guild.get_online_list()  # Получаем список онлайн-игроков
        if online_players:
            online_names = ", ".join(char.name for char in online_players)  # Преобразуем список Character в строку
            response = f"Онлайн сейчас ({len(online_players)} чел.): {online_names}"
        else:
            response = "Никто не в сети 😢"
        await update.message.reply_text(response)

    async def handle_setnick(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        glob.logger.info(f"Handle /setnick command from {update.effective_user.username or update.effective_user.first_name}")
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
        # Отправка сообщения в чат для канала GUILD
        if data.author.name is None:
            glob.logger.debug(f"Ignore SYSTEM message: {data.text}")
            return
        if data.channel != glob.codes.chat_channels.GUILD:
            glob.logger.debug(f"Ignore not GUILD message: {data.text}")
            return
        message_text = f"<{data.author.name}>: {self.parse_links(data.text)}"
        await self.application.bot.send_message(chat_id=self.chat_id,
                                                message_thread_id=self.message_thread_id,
                                                text=message_text,
                                                disable_notification=True)

    async def handle_ADD_CALENDAR_EVENT(self, data):
        glob.logger.info(f"ADD_CALENDAR_EVENT: {data}")

    async def handle_PURGE_CALENDAR(self, data):
        glob.logger.info(f"PURGE_CALENDAR: {data}")

    async def handle_ACTIVITY_UPDATE(self, data):
        pass

    async def handle_GUILD_EVENT(self, data):
        pass

    @staticmethod
    def parse_links(text):
        # Функция-заменитель для re.sub
        def repl(match):
            link_text = match.group("text")  # текст ссылки, например, "Моя любовь подобна алой розе"
            link_type = match.group("type")  # тип ссылки, например, "quest" или "achievement"
            obj_id = match.group("id")  # ID объекта, например, "1703"
            # Формируем Markdown-ссылку: [текст](ссылка)
            return f'[{link_text}]({glob.db}?{link_type}={obj_id})'

        # Заменяем все вхождения ссылки с помощью re.sub
        return re.sub(TelegramBot.LINK_PATTERN, repl, text)

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
