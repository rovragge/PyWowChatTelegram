import asyncio

from src.connector.base import Connector
from src.telegram_bot import TelegramBot


class TelegramConnector(Connector):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = TelegramBot(out_queue=self.out_queue)

    def get_handler(self):
        return None

    async def run(self):
        # Параллельно запускаем приём и отправку пакетов
        await asyncio.gather(self.receiver_coro(), self.sender_coro())

    async def receiver_coro(self):
        # Запускаем получение обновлений от Telegram
        await self.bot.start()

    async def sender_coro(self):
        while True:
            try:
                packet = await self.in_queue.get()
            except asyncio.exceptions.CancelledError:
                break
            else:
                await self.bot.handle_packet(packet)
