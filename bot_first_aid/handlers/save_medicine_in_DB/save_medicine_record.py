from telegram_data.models import TelegramMessage
from asgiref.sync import sync_to_async


# Асинхронная функция для сохранения записи в БД
async def save_medicine_record(name, expiry_date_str, expiry_date, DISEASE_GROUP_text, ORGAN_text, HTML_LINK_text, tablet_quantity):
    await sync_to_async(TelegramMessage.objects.create)(
        message_id="0",
        user_id="0",
        text=f"{name} - {expiry_date_str}",
        expiry_date=expiry_date,
        medicine_name=name,
        DISEASE_GROUP=DISEASE_GROUP_text,
        ORGAN=ORGAN_text,
        HTML_LINK=HTML_LINK_text,
        quantity=tablet_quantity
    )