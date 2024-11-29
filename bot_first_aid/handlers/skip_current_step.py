from bot_first_aid.globals import TYPING_EXPIRY_DATE, TYPING_ORGAN_GROUP
from bot_first_aid.handlers.skip_button import skip_button

async def skip_current_step(update, context, current_step, next_step, default_value, next_input_flag, prompt_text):
    """
    Универсальная функция для пропуска шага с отправкой сообщения и клавиатуры.

    :param update: Обновление от Telegram.
    :param context: Контекст с данными пользователя.
    :param current_step: Название текущего шага, из которого вызывается функция.
    :param next_step: Название следующего шага, куда нужно перейти.
    :param default_value: Значение по умолчанию, которое будет установлено в контексте.
    :param next_input_flag: Следующий флаг ввода, который нужно установить.
    :param prompt_text: Текст для запроса ввода (например, "Введите орган, который нужно лечить").
    """
    print("skip_step")
    # Устанавливаем значение по умолчанию для текущего шага
    context.user_data[current_step] = default_value
    context.user_data['awaiting_input'] = next_input_flag  # Обновляем флаг ожидания ввода

    create_choosing = False
    if next_step == TYPING_ORGAN_GROUP:
        create_choosing = True

    # Если следующий шаг - TYPING_EXPIRY_DATE, не создаем клавиатуру с кнопкой "Пропустить"
    if next_step != TYPING_EXPIRY_DATE:
        await skip_button(update, context, prompt_text, create_choosing)
    else:
        # Просто отправляем текст без клавиатуры, если следующий шаг TYPING_EXPIRY_DATE
        await update.message.reply_text(prompt_text)

    # Возвращаем следующий шаг
    return next_step