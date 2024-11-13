import os
import django
from dotenv import load_dotenv
import asyncio

# Устанавливаем настройки Django до импорта моделей
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telegram_project.settings')

# Инициализация Django
django.setup()

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from django.conf import settings
from telegram_data.models import TelegramMessage
from asgiref.sync import sync_to_async

# Загружаем переменные из .env файла
load_dotenv()

# Асинхронные обработчики
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Hello! Send me any message and I will save it.')

# Асинхронная функция для сохранения сообщения в базу данных
async def save_message(update: Update, context: CallbackContext) -> None:
    user_id = str(update.message.from_user.id)
    message_id = str(update.message.message_id)
    text = update.message.text

    # Сохраняем сообщение в базе данных
    await database_save_message(message_id, user_id, text)

    await update.message.reply_text(f"Your message: '{text}' has been saved!")

# Асинхронная функция для записи в базу данных
@sync_to_async
def database_save_message(message_id, user_id, text):
    TelegramMessage.objects.create(
        message_id=message_id,
        user_id=user_id,
        text=text
    )

# Главное асинхронное выполнение
async def main():
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_message))

    await application.run_polling()

# Используем стандартный цикл событий
if __name__ == '__main__':
    import nest_asyncio
    nest_asyncio.apply()  # Включаем поддержку вложенных событийных циклов
    # Запускаем основной асинхронный процесс
    asyncio.run(main())  # Вновь запускаем через asyncio.run, чтобы избежать предупреждения
