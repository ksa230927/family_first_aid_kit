from bot_first_aid.globals import TYPING_DISEASE_GROUP, CHOOSING
from bot_first_aid.handlers.skip_button import skip_button
from bot_first_aid.handlers.skip_current_step import skip_current_step
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler

# Обработка ввода органа, который лечит это лекарство
async def handle_ORGAN(update, context):
    print("handle_ORGAN")
    handle_ORGAN_text = "Не задано" if update.message.text == "Пропустить" else update.message.text
    text_in_chat_for_user = "Введите тип болезни или нажмите 'Пропустить':"

    # Если на предыдущем шаге была нажата кнопка "Пропустить"
    if update.message.text == "Пропустить":
        return await skip_current_step(
            update,
            context,
            'ORGAN',
            TYPING_DISEASE_GROUP,
            handle_ORGAN_text,
            'DISEASE_GROUP',
            text_in_chat_for_user
        )
    if update.message.text == "Выбрать из списка":
        # Переход к выбору органа из списка
        return await choose_organ_from_list(update, context)

    context.user_data['ORGAN'] = handle_ORGAN_text
    # дальше идет подготовка к переходу на следующий шаг
    await skip_button(update, context, text_in_chat_for_user, False)
    context.user_data['awaiting_input'] = 'DISEASE_GROUP'  # Обновляем флаг, что теперь ожидаем ввод типа болезни
    return TYPING_DISEASE_GROUP

# Эта функция отправляет список кнопок с органами.
async def choose_organ_from_list(update, context):
    print("choose_organ_from_list")
    # Список доступных органов
    organs = ["Голова", "Живот", "Позвоночник"]
    # Создаем клавиатуру с кнопками для каждого органа
    keyboard = [[InlineKeyboardButton(organ, callback_data=f"select_organ:{organ}")] for organ in organs]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите орган из списка:", reply_markup=reply_markup)
    return CHOOSING

# Эта функция обрабатывает выбор органа из списка.
async def handle_organ_selection(update, context):
    """
    Обрабатывает выбор органа из списка.
    """
    print("handle_organ_selection вызвана")
    # Проверяем, есть ли callback_query
    query = update.callback_query
    if query:
        try:
            # Извлекаем данные из callback_data
            selected_organ = query.data.split(":")[1]
            context.user_data['ORGAN'] = selected_organ

            # Уведомляем пользователя о выбранном органе
            await query.answer(f"Вы выбрали: {selected_organ}") # Если вы хотите только уведомление (краткое всплывающее сообщение):
            await query.message.reply_text(f"Вы выбрали: {selected_organ}") # Подходит для случаев, когда нужно сохранить историю действий пользователя в чате.

            # Переход к следующему шагу
            text_in_chat_for_user = "Введите тип болезни или нажмите 'Пропустить':"
            await skip_button(update, context, text_in_chat_for_user)
            context.user_data['awaiting_input'] = 'DISEASE_GROUP'

            return TYPING_DISEASE_GROUP

        except IndexError:
            # Обработка ошибок в случае некорректных данных
            await query.answer("Ошибка при выборе органа. Попробуйте еще раз.")
            return ConversationHandler.END
    else:
        # Если нет callback_query, выводим сообщение в консоль для отладки
        print("Ошибка: update.callback_query отсутствует")
        await update.message.reply_text(
            "Произошла ошибка. Попробуйте снова выбрать орган."
        )
        return ConversationHandler.END