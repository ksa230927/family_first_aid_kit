from bot_first_aid.globals import TYPING_EXPIRY_DATE, TYPING_HTML_LINK
from bot_first_aid.handlers.skip_button import skip_button
from datetime import datetime

# Обработка ввода срока годности
async def handle_expiry(update, context):
    print("handle_expiry")
    expiry_date_str = update.message.text
    text_in_chat_for_user = "Введите HTML ссылку на инструкцию к лекарству или нажмите 'Пропустить':"

    # Преобразование строки даты и проверка на корректность
    context.user_data['expiry_date_str'] = expiry_date_str
    expiry_date = parse_expiry_date(expiry_date_str)
    if expiry_date is None:
        await update.message.reply_text("Неверный формат даты. Пожалуйста, используйте формат дд.мм.гггг.")
        return TYPING_EXPIRY_DATE
    context.user_data['expiry_date'] = expiry_date

    # дальше идет подготовка к переходу на следующий шаг
    await skip_button(update, context, text_in_chat_for_user)
    context.user_data['awaiting_input'] = 'HTML_LINK'      # Обновляем флаг, что бот теперь ожидает HTML_LINK
    return TYPING_HTML_LINK

# Функция для преобразования строки даты
def parse_expiry_date(expiry_date_str):
    try:
        return datetime.strptime(expiry_date_str, "%d.%m.%Y").date()
    except ValueError:
        return None