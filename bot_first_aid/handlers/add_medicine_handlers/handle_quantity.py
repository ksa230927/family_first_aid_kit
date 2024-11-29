from bot_first_aid.globals import TYPING_quantity, TYPING_ORGAN_GROUP
from bot_first_aid.handlers.skip_button import skip_button

async def handle_quantity(update, context) -> int:
    print("handle_quantity")
    # Получаем введенное количество таблеток
    tablet_quantity = update.message.text
    text_in_chat_for_user = "Введите орган, который нужно лечить или нажмите 'Пропустить':"
    # Проверяем, является ли введенное значение целым числом
    if tablet_quantity.isdigit():
        context.user_data['tablet_quantity'] = int(tablet_quantity)
        await update.message.reply_text(f"Количество таблеток: {tablet_quantity}")
    else:
        await update.message.reply_text("Пожалуйста, введите целое положительное число для количества таблеток.")
        return TYPING_quantity

    # дальше идет подготовка к переходу на следующий шаг
    await skip_button(update, context, text_in_chat_for_user, True)
    context.user_data['awaiting_input'] = 'ORGAN'      # Обновляем флаг, что бот теперь ожидает орган, который нужно лечить
    return TYPING_ORGAN_GROUP