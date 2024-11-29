from bot_first_aid.globals import TYPING_EXPIRY_DATE
from bot_first_aid.handlers.skip_current_step import skip_current_step

# Обработка ввода типа заболевания
async def handle_DISEASE_GROUP(update, context):
    print("handle_DISEASE_GROUP")
    DISEASE_GROUP_text = "Не задано" if update.message.text == "Пропустить" else update.message.text
    text_in_chat_for_user = "Введите срок годности лекарства (например, 01.12.2024):"

    # Если нажата кнопка "Пропустить"
    if update.message.text == "Пропустить":
        # print('вызов skip_step из handle_DISEASE_GROUP')
        return await skip_current_step(
            update,
            context,
            'DISEASE_GROUP',
            TYPING_EXPIRY_DATE,
            DISEASE_GROUP_text,
            'expiry_date',
            text_in_chat_for_user
        )
    context.user_data['DISEASE_GROUP'] = DISEASE_GROUP_text
    # дальше идет подготовка к переходу на следующий шаг
    await update.message.reply_text(text_in_chat_for_user)
    context.user_data['awaiting_input'] = 'expiry_date'  # Обновляем флаг, что бот теперь ожидает дату
    return TYPING_EXPIRY_DATE