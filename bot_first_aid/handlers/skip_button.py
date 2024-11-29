from telegram import ReplyKeyboardMarkup

async def skip_button(update, context, request_text, choose_from_list=False):
    """
    Функция для отправки запроса с кнопкой "Пропустить"

    :param update: объект update из Telegram
    :param context: объект context из Telegram
    :param request_text: текст запроса, который будет отображаться пользователю
    """
    # Создаем клавиатуру с кнопкой "Пропустить"
    # Ветвление для выбора клавиатуры
    if choose_from_list:
        keyboard = [["Пропустить", "Выбрать из списка"]]  # Для этапа выбора органа
    else:
        keyboard = [["Пропустить"]]  # Для других этапов
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    # Проверяем тип update
    if update.message:  # Когда update содержит сообщение
        # Отправляем сообщение с запросом
        await update.message.reply_text(
            request_text,
            reply_markup=reply_markup
        )
    elif update.callback_query:  # Когда update содержит callback_query
        # Отправляем сообщение с запросом в ответ на callback_query
        await update.callback_query.message.reply_text(
            request_text,
            reply_markup=reply_markup
        )
        # Ответ на callback_query, чтобы не было индикатора загрузки
        await update.callback_query.answer()
