import textwrap

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from bot_first_aid.globals import CHOOSING
from telegram_data.models import TelegramMessage
from asgiref.sync import sync_to_async

async def handle_view_list(update, context):
    keyboard = [
        [InlineKeyboardButton("Показать полный список", callback_data='show_full_list')],
        [InlineKeyboardButton("Показать список ссылок", callback_data='show_links')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем сообщение с выбором действия
    await update.callback_query.message.reply_text(
        "Выберите вариант:",
        reply_markup=reply_markup
    )
    await update.callback_query.answer()  # Отвечаем на callback_query
    return CHOOSING

# Изменение обработчика callback_query: Теперь нам нужно добавить обработку разных кнопок,
# чтобы на основе выбранного варианта показывать полный список или только ссылки.
async def handle_callback_query(update, context):
    query = update.callback_query
    data = query.data

    if data == 'show_full_list':
        await view_full_list(update, context)
    elif data == 'show_links':
        await view_links(update, context)
    return CHOOSING

# Функция для отображения списка всех лекарств
async def view_full_list(update, context):
    medicines = await sync_to_async(list)(TelegramMessage.objects.all())

    if medicines:
        header = """
<pre>
<b>Название лекарства</b>   | <b>Срок годности</b>| <b>Кол-во</b> 
----------------------------------------
"""
        message_text = header
        messages = []
        max_name_width = 20  # Максимальная ширина для названия лекарства

        for medicine in medicines:
            # Переносим название лекарства
            medicine_name = medicine.medicine_name or "Не задано"
            wrapped_name = textwrap.wrap(medicine_name, width=max_name_width)
            name_block = "\n".join(f"{line:<{max_name_width}}" for line in wrapped_name)

            expiry_date = (str(medicine.expiry_date) or "Не задано").ljust(12)
            quantity = (str(medicine.quantity) if medicine.quantity is not None else "-").ljust(5)

            name_lines = name_block.split("\n")
            line = f"{name_lines[0]} | {expiry_date} | {quantity}\n"
            for additional_line in name_lines[1:]:
                line += f"{additional_line} |\n"  # Добавляем дополнительные строки с пустыми колонками

            # Проверяем длину сообщения, если приближаемся к лимиту, сохраняем текущий блок текста
            if len(message_text) + len(line) > 4000:
                messages.append(message_text + "</pre>")
                message_text = header  # Начинаем новое сообщение с заголовка

            message_text += line

        # Добавляем последнее сообщение
        if message_text:
            messages.append(message_text + "</pre>")
    else:
        messages = ["В базе данных нет лекарств."]

    # Отправляем каждое сообщение из списка
    await update.callback_query.answer()
    for text in messages:
        await update.callback_query.message.reply_text(text, parse_mode="HTML")

    return CHOOSING

# Функция для отображения списка ссылок (будет выполняться по кнопке "Показать список ссылок"):
async def view_links(update, context):
    medicines = await sync_to_async(list)(TelegramMessage.objects.all())

    if medicines:
        # Начинаем HTML-форматирование
        message_text = "<b>Список лекарств и ссылок:</b>\n\n"

        for medicine in medicines:
            medicine_name = medicine.medicine_name or "Не задано"
            html_link = medicine.HTML_LINK or "Не задано"

            # Проверяем, если ссылка задана, то выводим ссылку, если нет — текст
            if html_link != "Не задано":
                message_text += f"🔹 <b>{medicine_name}</b>: <a href='{html_link}'>{html_link}</a>\n\n"
            else:
                message_text += f"🔹 <b>{medicine_name}</b>: Ссылка не задана\n\n"

        # Закрываем HTML
        message_text += "<i>Для получения информации кликните на Перейти.</i>"
    else:
        message_text = "В базе данных нет лекарств."

    # Отправляем сообщение с ссылками
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(message_text, parse_mode="HTML", disable_web_page_preview=True)

    return CHOOSING
