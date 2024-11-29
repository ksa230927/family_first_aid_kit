from bot_first_aid.globals import TYPING_NAME

# Обработка нажатия кнопки "Добавить лекарство"
async def add_medicine(update, context):
    print("add_medicine")
    await update.callback_query.answer()  # Оповещаем о нажатии кнопки
    await update.callback_query.message.reply_text("Введите наименование лекарства:")
    context.user_data['awaiting_input'] = 'name'  # Устанавливаем флаг в context.user_data, что бот ожидает ввод наименования лекарства
    return TYPING_NAME