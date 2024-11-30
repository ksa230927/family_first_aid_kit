from bot_first_aid.globals import TYPING_quantity, TYPING_NAME
from telegram_data.models import TelegramMessage
from asgiref.sync import sync_to_async

# Обработка ввода наименования
async def handle_name(update, context):
    print("handle_name")
    name = update.message.text
    context.user_data['name'] = name
    text_in_chat_for_user = "Введите количество таблеток/доз:"

    # Проверка, есть ли уже такое лекарство в базе данных
    existing_medicine = await sync_to_async(lambda: TelegramMessage.objects.filter(medicine_name=name).first())()
    if existing_medicine:
        # Если лекарство уже существует, сообщаем об этом и возвращаем на этап TYPING_NAME
        await update.message.reply_text(f"Лекарство с наименованием '{name}' уже существует в базе данных.")
        return TYPING_NAME  # Возвращаем на этап выбора действия

    # дальше идет подготовка к переходу на следующий шаг
    await update.message.reply_text(text_in_chat_for_user)
    context.user_data['awaiting_input'] = 'quantity'      # Обновляем флаг, что бот теперь ожидает количество таблеток
    return TYPING_quantity