from telegram.ext import ConversationHandler

# Отмена процесса
async def cancel_input(update, context):
    print("cancel")
    await update.message.reply_text('Действие отменено.')
    # Снимаем флаг ожидания ввода
    if 'awaiting_input' in context.user_data:
        del context.user_data['awaiting_input']
    context.user_data.clear() # Очищаем user_data, если требуется
    return ConversationHandler.END