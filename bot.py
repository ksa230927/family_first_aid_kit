import os
import django
from dotenv import load_dotenv

# Устанавливаем настройки Django до импорта моделей
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telegram_project.settings')

# Инициализация Django
django.setup()

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters
from django.conf import settings
from telegram_data.models import TelegramMessage
from asgiref.sync import sync_to_async
from datetime import datetime

# Загружаем переменные из .env файла
load_dotenv()

# Состояния для ConversationHandler
CHOOSING, TYPING_NAME, TYPING_EXPIRY_DATE = range(3)

# Кнопки для inline-клавиатуры
async def start(update, context):
    print("start")
    keyboard = [[InlineKeyboardButton("Добавить лекарство", callback_data='add_medicine')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Отправляем приветственное сообщение с кнопкой
    await update.message.reply_text('Привет! Выберите действие:', reply_markup=reply_markup)
    # Устанавливаем флаг в context.user_data, чтобы напоминать пользователю
    context.user_data['awaiting_input'] = 'button'  # Ожидаем нажатие кнопки

    return CHOOSING

# Обработка нажатия кнопки "Добавить лекарство"
async def add_medicine(update, context):
    print("add_medicine")
    await update.callback_query.answer()  # Оповещаем о нажатии кнопки
    await update.callback_query.message.reply_text("Введите наименование лекарства:")
    # Устанавливаем флаг в context.user_data, что бот ожидает ввод
    context.user_data['awaiting_input'] = 'name'  # Ожидаем наименование лекарства
    return TYPING_NAME

# Обработка ввода наименования
async def handle_name(update, context):
    print("handle_name")
    name = update.message.text
    context.user_data['name'] = name
    # Проверка, есть ли уже такое лекарство в базе данных
    existing_medicine = await sync_to_async(lambda: TelegramMessage.objects.filter(medicine_name=name).first())()

    if existing_medicine:
        # Если лекарство уже существует, сообщаем об этом и возвращаем на этап CHOOSING
        await update.message.reply_text(f"Лекарство с наименованием '{name}' уже существует в базе данных.")
        return TYPING_NAME  # Возвращаем на этап выбора действия

    await update.message.reply_text("Введите срок годности лекарства (например, 01/12/2024):")
    # Обновляем флаг, что бот теперь ожидает дату
    context.user_data['awaiting_input'] = 'expiry_date'  # Ожидаем дату
    return TYPING_EXPIRY_DATE

# Обработка ввода срока годности
async def handle_expiry(update, context):
    print("handle_expiry")
    name = context.user_data['name']
    expiry_date_str = update.message.text

    # Преобразование строки даты в формат YYYY-MM-DD
    try:
        expiry_date = datetime.strptime(expiry_date_str, "%d/%m/%Y").date()
    except ValueError:
        await update.message.reply_text("Неверный формат даты. Пожалуйста, используйте формат дд/мм/гггг.")
        return TYPING_EXPIRY_DATE

    # Сохранение данных в базе данных с использованием sync_to_async
    await sync_to_async(TelegramMessage.objects.create)(
        message_id="0",
        user_id="0",
        text=f"{name} - {expiry_date_str}",
        expiry_date=expiry_date,
        medicine_name=name
    )

    # Завершаем процесс ввода
    await update.message.reply_text(f"Лекарство '{name}' добавлено. Срок годности: {expiry_date_str}.")
    # Снимаем флаг ожидания ввода
    del context.user_data['awaiting_input']
    return ConversationHandler.END

# Отмена процесса
async def cancel(update, context):
    print("cancel")
    await update.message.reply_text('Действие отменено.')
    # Снимаем флаг ожидания ввода
    if 'awaiting_input' in context.user_data:
        del context.user_data['awaiting_input']
    return ConversationHandler.END

# Обработка текста, если кнопка не нажата
async def handle_message(update, context):
    print("handle_message")
    # Проверяем, если ожидаем нажатие кнопки
    if context.user_data.get('awaiting_input') == 'button':
        await update.message.reply_text("Пожалуйста, нажмите кнопку 'Добавить лекарство'.")
    return CHOOSING

# Главная функция с обработчиками
def main():
    # Создаем экземпляр приложения бота
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Определяем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start), # Обработка команды /start
            MessageHandler(filters.TEXT & ~filters.COMMAND, start) # Обработка любого текстового сообщения
        ],
        states={
            CHOOSING: [
                CallbackQueryHandler(add_medicine, pattern='^add_medicine$'),
                # Обработка нажатия кнопки "Добавить лекарство"
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)  # Обработка любого текстового сообщения
            ],
            TYPING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
            TYPING_EXPIRY_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_expiry)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Добавляем обработчик к приложению
    application.add_handler(conv_handler)

    # Добавляем обработчик для всех текстовых сообщений
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
