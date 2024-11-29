from bot_first_aid.handlers.save_medicine_in_DB.save_medicine_record import save_medicine_record
from telegram.ext import ConversationHandler
async def handle_save_record(update, context):
    print("handle_save_record")
    name = context.user_data['name']
    DISEASE_GROUP_text = context.user_data['DISEASE_GROUP']
    ORGAN_text = context.user_data['ORGAN']
    expiry_date_str = context.user_data['expiry_date_str']
    expiry_date = context.user_data['expiry_date']
    HTML_LINK_text = context.user_data['HTML_LINK_text']
    tablet_quantity = context.user_data['tablet_quantity']

    # Сохранение записи в базе данных
    await save_medicine_record(name, expiry_date_str, expiry_date, DISEASE_GROUP_text, ORGAN_text, HTML_LINK_text, tablet_quantity)

    # Завершаем процесс ввода
    await update.message.reply_text(f"Лекарство '{name}' добавлено. Срок годности: {expiry_date_str}.")
    # Снимаем флаг ожидания ввода
    del context.user_data['awaiting_input']
    return ConversationHandler.END