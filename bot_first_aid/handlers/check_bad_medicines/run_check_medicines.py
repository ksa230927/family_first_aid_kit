import asyncio
from bot_first_aid.handlers.check_bad_medicines.check_medicines import check_medicines
from types import SimpleNamespace
from telegram import Bot
from bot_first_aid.globals import chat_ids
from django.conf import settings

class DummyCallbackQuery:
    # async def answer(self, text=None, show_alert=False):
    #     print(f"Ответ на callback: {text}")

    def __init__(self, bot, chat_ids):
        self.bot = bot
        self.chat_ids = chat_ids

    async def answer(self, text=None, show_alert=False):
        if text:
            for chat_id in self.chat_ids:
                await self.bot.send_message(chat_id=chat_id, text=text)

def run_check_medicines():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    # Используем токен для создания бота
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

    # print(chat_ids)

    # Создаем фиктивные update и context
    dummy_update = SimpleNamespace(callback_query=DummyCallbackQuery(bot, chat_ids))
    dummy_context = SimpleNamespace(bot=bot)  # Передаём бота явно

    loop.run_until_complete(check_medicines(dummy_update, dummy_context))