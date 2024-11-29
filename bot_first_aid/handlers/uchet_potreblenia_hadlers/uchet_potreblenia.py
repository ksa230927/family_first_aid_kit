import os
import django

# Устанавливаем переменную окружения для настроек
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')  # Замените 'myproject.settings' на имя вашего модуля настроек

# Инициализация Django
django.setup()

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from bot_first_aid.globals import CHOOSING
from telegram_data.models import TelegramMessage
from asgiref.sync import sync_to_async

async def uchet_potreblenia(update, context):

    medicine_names = await sync_to_async(list)(TelegramMessage.objects.values_list('medicine_name', flat=True))

    # Создаём кнопки для каждого наименования
    keyboard = [
        [InlineKeyboardButton(name, callback_data=f'medicine:{name}')]
        for name in medicine_names
    ]
    # Генерируем клавиатуру
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем сообщение с динамически созданными кнопками
    await update.callback_query.message.reply_text(
        "Выберите лекарство:",
        reply_markup=reply_markup
    )
    await update.callback_query.answer()  # Отвечаем на callback_query
    return CHOOSING
    # keyboard = [
    #     [InlineKeyboardButton("Показать полный список", callback_data='show_full_list')],
    #     [InlineKeyboardButton("Показать список ссылок", callback_data='show_links')]
    # ]
    # reply_markup = InlineKeyboardMarkup(keyboard)
    #
    # # Отправляем сообщение с выбором действия
    # await update.callback_query.message.reply_text(
    #     "Выберите вариант:",
    #     reply_markup=reply_markup
    # )
    # await update.callback_query.answer()  # Отвечаем на callback_query
    # return CHOOSING

