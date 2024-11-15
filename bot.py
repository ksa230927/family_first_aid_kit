import os
import django
from dotenv import load_dotenv

# Устанавливаем настройки Django до импорта моделей
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telegram_project.settings')

# Инициализация Django
django.setup()

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters
from django.conf import settings
from telegram_data.models import TelegramMessage
from asgiref.sync import sync_to_async
from datetime import datetime

# Загружаем переменные из .env файла
load_dotenv()

# Состояния для ConversationHandler
CHOOSING, TYPING_NAME, TYPING_EXPIRY_DATE, TYPING_DISEASE_GROUP, TYPING_ORGAN_GROUP, SAVE_RECORD_IN_DB, TYPING_HTML_LINK = range(7)

# Кнопки для inline-клавиатуры
async def start(update, context):
    print("start")
    keyboard = [[InlineKeyboardButton("Добавить лекарство", callback_data='add_medicine')],
                [InlineKeyboardButton("Просмотреть весь список", callback_data='view_list')]
                ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Отправляем приветственное сообщение с кнопкой
    await update.message.reply_text('Привет! Выберите действие:', reply_markup=reply_markup)
    # Устанавливаем флаг в context.user_data, чтобы напоминать пользователю
    context.user_data['awaiting_input'] = 'button'  # Ожидаем нажатие кнопки

    return CHOOSING

# Обработка нажатия кнопки "Добавить лекарство"
async def add_medicine(update, context):
    print("add_medicine")
    await update.callback_query.answer()  # Оповещаем о нажатии кнопки
    await update.callback_query.message.reply_text("Введите наименование лекарства:")
    # Устанавливаем флаг в context.user_data, что бот ожидает ввод
    context.user_data['awaiting_input'] = 'name'  # Ожидаем наименование лекарства
    return TYPING_NAME

# Функция для отображения списка всех лекарств
async def view_list(update, context):
    print("view_list")

    medicines = await sync_to_async(list)(TelegramMessage.objects.all())

    if medicines:
        header = """
<pre>
<b>Название лекарства</b>             | <b>Срок годности</b>             | <b>Тип болезни</b>              | <b>Орган</b> 
------------------------------------------------------------------------------------------
"""
        message_text = header
        messages = []

        for medicine in medicines:
            medicine_name = (medicine.medicine_name or "Не указано").ljust(30)
            expiry_date = (str(medicine.expiry_date) or "Не указано").ljust(25)
            disease_group = (medicine.DISEASE_GROUP or "Не указано").ljust(25)
            ORGAN = (medicine.ORGAN or "Не указано").ljust(25)

            line = f"{medicine_name:<25} | {expiry_date:<15} | {disease_group:<20}| {ORGAN:<20}\n"
            # Проверяем длину сообщения, если приближаемся к лимиту, сохраняем текущий блок текста
            if len(message_text) + len(line) > 4000:
                messages.append(message_text + "</pre>")
                message_text = header  # Начинаем новое сообщение с заголовка

            message_text += line

        # Добавляем последнее сообщение
        if message_text:
            messages.append(message_text + "</pre>")
    else:
        messages = ["В базе данных нет лекарств."]

    # Отправляем каждое сообщение из списка
    await update.callback_query.answer()
    for text in messages:
        await update.callback_query.message.reply_text(text, parse_mode="HTML")

    return CHOOSING

# Обработка ввода наименования
async def handle_name(update, context):
    print("handle_name")
    name = update.message.text
    context.user_data['name'] = name
    # Проверка, есть ли уже такое лекарство в базе данных
    existing_medicine = await sync_to_async(lambda: TelegramMessage.objects.filter(medicine_name=name).first())()

    if existing_medicine:
        # Если лекарство уже существует, сообщаем об этом и возвращаем на этап TYPING_NAME
        await update.message.reply_text(f"Лекарство с наименованием '{name}' уже существует в базе данных.")
        return TYPING_NAME  # Возвращаем на этап выбора действия

    await update.message.reply_text("Введите орган, который нужно лечить:")
    # Обновляем флаг, что бот теперь ожидает орган, который нужно лечить
    context.user_data['awaiting_input'] = 'ORGAN'  # Ожидаем орган, который нужно лечить
    return TYPING_ORGAN_GROUP

# Обработка ввода органа, который лечит это лекарство
async def handle_ORGAN(update, context):
    print("handle_ORGAN")
    handle_ORGAN_text = update.message.text
    context.user_data['ORGAN'] = handle_ORGAN_text

    await update.message.reply_text("Введите тип болезни:")
    # Обновляем флаг, что бот теперь ожидает дату
    context.user_data['awaiting_input'] = 'DISEASE_GROUP'  # Ожидаем дату
    return TYPING_DISEASE_GROUP

# Обработка ввода типа заболевания
async def handle_DISEASE_GROUP(update, context):
    print("handle_DISEASE_GROUP")
    DISEASE_GROUP_text = update.message.text
    context.user_data['DISEASE_GROUP'] = DISEASE_GROUP_text

    await update.message.reply_text("Введите срок годности лекарства (например, 01/12/2024):")
    # Обновляем флаг, что бот теперь ожидает дату
    context.user_data['awaiting_input'] = 'expiry_date'  # Ожидаем дату
    return TYPING_EXPIRY_DATE

# Обработка ввода срока годности
async def handle_expiry(update, context):
    print("handle_expiry")
    expiry_date_str = update.message.text
    context.user_data['expiry_date_str'] = expiry_date_str

    # Преобразование строки даты
    expiry_date = parse_expiry_date(expiry_date_str)
    if expiry_date is None:
        await update.message.reply_text("Неверный формат даты. Пожалуйста, используйте формат дд/мм/гггг.")
        return TYPING_EXPIRY_DATE

    context.user_data['expiry_date'] = expiry_date

    await update.message.reply_text("Введите HTML ссылку на инструкцию к лекарству:")
    # Обновляем флаг, что бот теперь ожидает дату
    context.user_data['awaiting_input'] = 'HTML_LINK'  # Ожидаем дату

    return TYPING_HTML_LINK

    # Автоматически вызываем handle_save_record
    # return await handle_html_link(update, context)

async def handle_html_link(update, context):
    print("handle_html_link")
    HTML_LINK_text = update.message.text
    context.user_data['HTML_LINK_text'] = HTML_LINK_text

    # Снимаем флаг ожидания ввода
    context.user_data['awaiting_input'] = 'save_record'

    # Автоматически вызываем handle_save_record
    return await handle_save_record(update, context)

async def handle_save_record(update, context):
    print("handle_save_record")
    name = context.user_data['name']
    DISEASE_GROUP_text = context.user_data['DISEASE_GROUP']
    ORGAN_text = context.user_data['ORGAN']
    expiry_date_str = context.user_data['expiry_date_str']
    expiry_date = context.user_data['expiry_date']
    HTML_LINK_text = context.user_data['HTML_LINK_text']

    # Сохранение записи в базе данных
    await save_medicine_record(name, expiry_date_str, expiry_date, DISEASE_GROUP_text, ORGAN_text, HTML_LINK_text)

    # Завершаем процесс ввода
    await update.message.reply_text(f"Лекарство '{name}' добавлено. Срок годности: {expiry_date_str}.")
    # Снимаем флаг ожидания ввода
    del context.user_data['awaiting_input']
    return ConversationHandler.END

# Асинхронная функция для сохранения записи в БД
async def save_medicine_record(name, expiry_date_str, expiry_date, DISEASE_GROUP_text, ORGAN_text, HTML_LINK_text):
    await sync_to_async(TelegramMessage.objects.create)(
        message_id="0",
        user_id="0",
        text=f"{name} - {expiry_date_str}",
        expiry_date=expiry_date,
        medicine_name=name,
        DISEASE_GROUP=DISEASE_GROUP_text,
        ORGAN=ORGAN_text,
        HTML_LINK=HTML_LINK_text
    )

# Функция для преобразования строки даты
def parse_expiry_date(expiry_date_str):
    try:
        return datetime.strptime(expiry_date_str, "%d/%m/%Y").date()
    except ValueError:
        return None

# Отмена процесса
async def cancel(update, context):
    print("cancel")
    await update.message.reply_text('Действие отменено.')
    # Снимаем флаг ожидания ввода
    if 'awaiting_input' in context.user_data:
        del context.user_data['awaiting_input']
    return ConversationHandler.END

# Обработка текста, если кнопка не нажата
async def handle_message(update, context):
    print("handle_message")
    # Проверяем, если ожидаем нажатие кнопки
    if context.user_data.get('awaiting_input') == 'button':
        # Создаем клавиатуру с кнопками
        keyboard = [
            [InlineKeyboardButton("Добавить лекарство", callback_data='add_medicine')],
            [InlineKeyboardButton("Просмотреть весь список", callback_data='view_list')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Отправляем приветственное сообщение с кнопкой
        await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
    return CHOOSING

# Главная функция с обработчиками
def main():
    # Создаем экземпляр приложения бота
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Определяем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start), # Обработка команды /start
            MessageHandler(filters.TEXT & ~filters.COMMAND, start) # Обработка любого текстового сообщения
        ],
        states={
            CHOOSING: [
                CallbackQueryHandler(add_medicine, pattern='^add_medicine$'),
                CallbackQueryHandler(view_list, pattern='^view_list$'),
                # Обработка нажатия кнопки "Добавить лекарство"
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)  # Обработка любого текстового сообщения
            ],
            TYPING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
            TYPING_ORGAN_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ORGAN)],
            TYPING_DISEASE_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_DISEASE_GROUP)],
            TYPING_EXPIRY_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_expiry)],
            TYPING_HTML_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_html_link)],
            SAVE_RECORD_IN_DB: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_save_record)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Добавляем обработчик к приложению
    application.add_handler(conv_handler)

    # Добавляем обработчик для всех текстовых сообщений
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
