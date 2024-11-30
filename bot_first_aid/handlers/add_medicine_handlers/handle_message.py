from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from bot_first_aid.globals import CHOOSING

# Обработка текста, если кнопка не нажата
async def handle_message(update, context):
    print("handle_message")
    # Проверяем, если ожидаем нажатие кнопки
    if context.user_data.get('awaiting_input') == 'button':
        # Создаем клавиатуру с кнопками
        keyboard = [
            [InlineKeyboardButton("Добавить лекарство", callback_data='add_medicine')],
            [InlineKeyboardButton("Учет потребления", callback_data='uchet_potreblenia_vibor')],
            [InlineKeyboardButton("Просмотреть весь список", callback_data='view_list')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Отправляем приветственное сообщение с кнопкой
        await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
    return CHOOSING