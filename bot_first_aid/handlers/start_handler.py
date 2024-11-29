from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot_first_aid.globals import chat_ids, CHOOSING

# Стартовая функция
async def start(update, context):
    chat_id = update.message.chat_id
    chat_ids.add(chat_id)
    print("start")
    keyboard = [[InlineKeyboardButton("Добавить лекарство", callback_data='add_medicine')],
                [InlineKeyboardButton("Учет потребления", callback_data='uchet_potreblenia')],
                [InlineKeyboardButton("Просмотреть весь список", callback_data='view_list')]
                ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Отправляем приветственное сообщение с кнопкой
    await update.message.reply_text('Привет! Выберите действие:', reply_markup=reply_markup)
    # Устанавливаем флаг в context.user_data, чтобы напоминать пользователю
    context.user_data['awaiting_input'] = 'button'  # Ожидаем нажатие кнопки
    return CHOOSING