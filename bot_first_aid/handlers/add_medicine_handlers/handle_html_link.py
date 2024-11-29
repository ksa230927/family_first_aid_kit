from bot_first_aid.handlers.save_medicine_in_DB.handle_save_record import handle_save_record

async def handle_html_link(update, context):
    print("handle_html_link")
    HTML_LINK_text = "Не задано" if update.message.text == "Пропустить" else update.message.text
    context.user_data['HTML_LINK_text'] = HTML_LINK_text

    # Снимаем флаг ожидания ввода
    context.user_data['awaiting_input'] = 'save_record'

    # Автоматически вызываем handle_save_record
    return await handle_save_record(update, context)