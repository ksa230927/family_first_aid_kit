from telegram_data.models import TelegramMessage
from asgiref.sync import sync_to_async
from telegram import Bot
from django.conf import settings
from bot_first_aid.globals import chat_ids

async def check_medicines(update, context):
    print("check_medicines")
    # Получаем лекарства, количество которых меньше 3
    # Используем sync_to_async для выполнения синхронного запроса в асинхронном контексте
    low_quantity_medicines = await sync_to_async(list)(TelegramMessage.objects.filter(quantity__lt=3).values_list('medicine_name', flat=True))

    if low_quantity_medicines:
        message = "Лекарства, количество которых меньше 3:\n" + "\n".join(low_quantity_medicines)
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

        for chat_id in chat_ids:  # Предполагается, что chat_ids определён и доступен
            await bot.send_message(chat_id=chat_id, text=message)
        await update.callback_query.answer("Сообщение отправлено всем пользователям.")
    else:
        await update.callback_query.answer("Все лекарства в достаточном количестве.")