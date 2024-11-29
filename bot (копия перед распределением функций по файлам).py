import os
import django
from dotenv import load_dotenv
import textwrap

# Устанавливаем настройки Django до импорта моделей
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telegram_project.settings')

# Инициализация Django
django.setup()


from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters
from django.conf import settings
from telegram_data.models import TelegramMessage
from asgiref.sync import sync_to_async
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import threading
import asyncio
from bot_first_aid.handlers.start_handler import start
# from bot.handlers.medicine_handlers import add_medicine
# from bot.handlers.disease_handlers import handle_DISEASE_GROUP
# from bot.scheduler_tasks import run_check_medicines
from bot_first_aid.globals import chat_ids, CHOOSING, TYPING_NAME, TYPING_EXPIRY_DATE, TYPING_DISEASE_GROUP, \
    TYPING_ORGAN_GROUP, SAVE_RECORD_IN_DB, TYPING_HTML_LINK, TYPING_quantity

# Инициализируем планировщик
scheduler = BackgroundScheduler()

# Загружаем переменные из .env файла
load_dotenv()

# Состояния для ConversationHandler
(CHOOSING,
 TYPING_NAME,
 TYPING_EXPIRY_DATE,
 TYPING_DISEASE_GROUP,
 TYPING_ORGAN_GROUP,
 SAVE_RECORD_IN_DB,
 TYPING_HTML_LINK,
 TYPING_quantity) = range(8)

# Глобальная переменная для хранения chat_id всех пользователей
chat_ids = set()

async def check_medicines():
    print("check_medicines")
    # Получаем лекарства, количество которых меньше 3
    # Используем sync_to_async для выполнения синхронного запроса в асинхронном контексте
    low_quantity_medicines = await sync_to_async(list)(TelegramMessage.objects.filter(quantity__lt=3).values_list('medicine_name', flat=True))

    if low_quantity_medicines:
        # Формируем сообщение
        message = "Лекарства, количество которых меньше 3:\n" + "\n".join(low_quantity_medicines)
        # Отправляем сообщение в чат-бот
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        # Отправляем сообщение всем пользователям
        for chat_id in chat_ids:
            await bot.send_message(chat_id=chat_id, text=message)

# # Стартовая функция
# async def start(update, context):
#     chat_id = update.message.chat_id
#     chat_ids.add(chat_id)
#     print("start")
#     keyboard = [[InlineKeyboardButton("Добавить лекарство", callback_data='add_medicine')],
#                 [InlineKeyboardButton("Просмотреть весь список", callback_data='view_list')]
#                 ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     # Отправляем приветственное сообщение с кнопкой
#     await update.message.reply_text('Привет! Выберите действие:', reply_markup=reply_markup)
#     # Устанавливаем флаг в context.user_data, чтобы напоминать пользователю
#     context.user_data['awaiting_input'] = 'button'  # Ожидаем нажатие кнопки
#     return CHOOSING

async def handle_view_list(update, context):
    keyboard = [
        [InlineKeyboardButton("Показать полный список", callback_data='show_full_list')],
        [InlineKeyboardButton("Показать список ссылок", callback_data='show_links')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем сообщение с выбором действия
    await update.callback_query.message.reply_text(
        "Выберите вариант:",
        reply_markup=reply_markup
    )
    await update.callback_query.answer()  # Отвечаем на callback_query
    return CHOOSING

# Изменение обработчика callback_query: Теперь нам нужно добавить обработку разных кнопок,
# чтобы на основе выбранного варианта показывать полный список или только ссылки.
async def handle_callback_query(update, context):
    query = update.callback_query
    data = query.data

    if data == 'show_full_list':
        await view_list(update, context)
    elif data == 'show_links':
        await view_links(update, context)
    return CHOOSING

# Функция для отображения списка всех лекарств
async def view_list(update, context):
    medicines = await sync_to_async(list)(TelegramMessage.objects.all())

    if medicines:
        header = """
<pre>
<b>Название лекарства</b>   | <b>Срок годности</b>| <b>Кол-во</b> 
----------------------------------------
"""
        message_text = header
        messages = []
        max_name_width = 20  # Максимальная ширина для названия лекарства

        for medicine in medicines:
            # Переносим название лекарства
            medicine_name = medicine.medicine_name or "Не задано"
            wrapped_name = textwrap.wrap(medicine_name, width=max_name_width)
            name_block = "\n".join(f"{line:<{max_name_width}}" for line in wrapped_name)

            expiry_date = (str(medicine.expiry_date) or "Не задано").ljust(12)
            quantity = (str(medicine.quantity) if medicine.quantity is not None else "-").ljust(5)

            name_lines = name_block.split("\n")
            line = f"{name_lines[0]} | {expiry_date} | {quantity}\n"
            for additional_line in name_lines[1:]:
                line += f"{additional_line} |\n"  # Добавляем дополнительные строки с пустыми колонками

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

# Функция для отображения списка ссылок (будет выполняться по кнопке "Показать список ссылок"):
async def view_links(update, context):
    medicines = await sync_to_async(list)(TelegramMessage.objects.all())

    if medicines:
        # Начинаем HTML-форматирование
        message_text = "<b>Список лекарств и ссылок:</b>\n\n"

        for medicine in medicines:
            medicine_name = medicine.medicine_name or "Не задано"
            html_link = medicine.HTML_LINK or "Не задано"

            # Проверяем, если ссылка задана, то выводим ссылку, если нет — текст
            if html_link != "Не задано":
                message_text += f"🔹 <b>{medicine_name}</b>: <a href='{html_link}'>{html_link}</a>\n\n"
            else:
                message_text += f"🔹 <b>{medicine_name}</b>: Ссылка не задана\n\n"

        # Закрываем HTML
        message_text += "<i>Для получения информации кликните на Перейти.</i>"
    else:
        message_text = "В базе данных нет лекарств."

    # Отправляем сообщение с ссылками
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(message_text, parse_mode="HTML", disable_web_page_preview=True)

    return CHOOSING

# Обработка нажатия кнопки "Добавить лекарство"
async def add_medicine(update, context):
    print("add_medicine")
    await update.callback_query.answer()  # Оповещаем о нажатии кнопки
    await update.callback_query.message.reply_text("Введите наименование лекарства:")
    context.user_data['awaiting_input'] = 'name'  # Устанавливаем флаг в context.user_data, что бот ожидает ввод наименования лекарства
    return TYPING_NAME

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

async def handle_quantity(update, context) -> int:
    print("handle_quantity")
    # Получаем введенное количество таблеток
    tablet_quantity = update.message.text
    text_in_chat_for_user = "Введите орган, который нужно лечить или нажмите 'Пропустить':"
    # Проверяем, является ли введенное значение целым числом
    if tablet_quantity.isdigit():
        context.user_data['tablet_quantity'] = int(tablet_quantity)
        await update.message.reply_text(f"Количество таблеток: {tablet_quantity}")
    else:
        await update.message.reply_text("Пожалуйста, введите целое положительное число для количества таблеток.")
        return TYPING_quantity

    # дальше идет подготовка к переходу на следующий шаг
    await skip_button(update, context, text_in_chat_for_user, True)
    context.user_data['awaiting_input'] = 'ORGAN'      # Обновляем флаг, что бот теперь ожидает орган, который нужно лечить
    return TYPING_ORGAN_GROUP

# Обработка ввода органа, который лечит это лекарство
async def handle_ORGAN(update, context):
    print("handle_ORGAN")
    handle_ORGAN_text = "Не задано" if update.message.text == "Пропустить" else update.message.text
    text_in_chat_for_user = "Введите тип болезни или нажмите 'Пропустить':"

    # Если на предыдущем шаге была нажата кнопка "Пропустить"
    if update.message.text == "Пропустить":
        return await skip_current_step(
            update,
            context,
            'ORGAN',
            TYPING_DISEASE_GROUP,
            handle_ORGAN_text,
            'DISEASE_GROUP',
            text_in_chat_for_user
        )
    if update.message.text == "Выбрать из списка":
        # Переход к выбору органа из списка
        return await choose_organ_from_list(update, context)

    context.user_data['ORGAN'] = handle_ORGAN_text
    # дальше идет подготовка к переходу на следующий шаг
    await skip_button(update, context, text_in_chat_for_user, False)
    context.user_data['awaiting_input'] = 'DISEASE_GROUP'  # Обновляем флаг, что теперь ожидаем ввод типа болезни
    return TYPING_DISEASE_GROUP

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

async def skip_button(update, context, request_text, choose_from_list=False):
    """
    Функция для отправки запроса с кнопкой "Пропустить"

    :param update: объект update из Telegram
    :param context: объект context из Telegram
    :param request_text: текст запроса, который будет отображаться пользователю
    """
    # Создаем клавиатуру с кнопкой "Пропустить"
    # Ветвление для выбора клавиатуры
    if choose_from_list:
        keyboard = [["Пропустить", "Выбрать из списка"]]  # Для этапа выбора органа
    else:
        keyboard = [["Пропустить"]]  # Для других этапов
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    # Проверяем тип update
    if update.message:  # Когда update содержит сообщение
        # Отправляем сообщение с запросом
        await update.message.reply_text(
            request_text,
            reply_markup=reply_markup
        )
    elif update.callback_query:  # Когда update содержит callback_query
        # Отправляем сообщение с запросом в ответ на callback_query
        await update.callback_query.message.reply_text(
            request_text,
            reply_markup=reply_markup
        )
        # Ответ на callback_query, чтобы не было индикатора загрузки
        await update.callback_query.answer()

# Обработка ввода типа заболевания
async def handle_DISEASE_GROUP(update, context):
    print("handle_DISEASE_GROUP")
    DISEASE_GROUP_text = "Не задано" if update.message.text == "Пропустить" else update.message.text
    text_in_chat_for_user = "Введите срок годности лекарства (например, 01.12.2024):"

    # Если нажата кнопка "Пропустить"
    if update.message.text == "Пропустить":
        # print('вызов skip_step из handle_DISEASE_GROUP')
        return await skip_current_step(
            update,
            context,
            'DISEASE_GROUP',
            TYPING_EXPIRY_DATE,
            DISEASE_GROUP_text,
            'expiry_date',
            text_in_chat_for_user
        )
    context.user_data['DISEASE_GROUP'] = DISEASE_GROUP_text
    # дальше идет подготовка к переходу на следующий шаг
    await update.message.reply_text(text_in_chat_for_user)
    context.user_data['awaiting_input'] = 'expiry_date'  # Обновляем флаг, что бот теперь ожидает дату
    return TYPING_EXPIRY_DATE

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

async def handle_html_link(update, context):
    print("handle_html_link")
    HTML_LINK_text = "Не задано" if update.message.text == "Пропустить" else update.message.text
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
    tablet_quantity = context.user_data['tablet_quantity']

    # Сохранение записи в базе данных
    await save_medicine_record(name, expiry_date_str, expiry_date, DISEASE_GROUP_text, ORGAN_text, HTML_LINK_text, tablet_quantity)

    # Завершаем процесс ввода
    await update.message.reply_text(f"Лекарство '{name}' добавлено. Срок годности: {expiry_date_str}.")
    # Снимаем флаг ожидания ввода
    del context.user_data['awaiting_input']
    return ConversationHandler.END

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

# Функция для преобразования строки даты
def parse_expiry_date(expiry_date_str):
    try:
        return datetime.strptime(expiry_date_str, "%d.%m.%Y").date()
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

# Эта функция обрабатывает выбор органа из списка.
async def handle_organ_selection(update, context):
    """
    Обрабатывает выбор органа из списка.
    """
    print("handle_organ_selection вызвана")
    # Проверяем, есть ли callback_query
    query = update.callback_query
    if query:
        try:
            # Извлекаем данные из callback_data
            selected_organ = query.data.split(":")[1]
            context.user_data['ORGAN'] = selected_organ

            # Уведомляем пользователя о выбранном органе
            await query.answer(f"Вы выбрали: {selected_organ}") # Если вы хотите только уведомление (краткое всплывающее сообщение):
            await query.message.reply_text(f"Вы выбрали: {selected_organ}") # Подходит для случаев, когда нужно сохранить историю действий пользователя в чате.

            # Переход к следующему шагу
            text_in_chat_for_user = "Введите тип болезни или нажмите 'Пропустить':"
            await skip_button(update, context, text_in_chat_for_user)
            context.user_data['awaiting_input'] = 'DISEASE_GROUP'

            return TYPING_DISEASE_GROUP

        except IndexError:
            # Обработка ошибок в случае некорректных данных
            await query.answer("Ошибка при выборе органа. Попробуйте еще раз.")
            return ConversationHandler.END
    else:
        # Если нет callback_query, выводим сообщение в консоль для отладки
        print("Ошибка: update.callback_query отсутствует")
        await update.message.reply_text(
            "Произошла ошибка. Попробуйте снова выбрать орган."
        )
        return ConversationHandler.END

# Эта функция отправляет список кнопок с органами.
async def choose_organ_from_list(update, context):
    print("choose_organ_from_list")
    # Список доступных органов
    organs = ["Голова", "Живот", "Позвоночник"]
    # Создаем клавиатуру с кнопками для каждого органа
    keyboard = [[InlineKeyboardButton(organ, callback_data=f"select_organ:{organ}")] for organ in organs]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите орган из списка:", reply_markup=reply_markup)
    return CHOOSING

def run_check_medicines():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(check_medicines())

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
                CallbackQueryHandler(handle_view_list, pattern='^view_list$'),
                CallbackQueryHandler(handle_callback_query, pattern='^show_full_list$'),
                CallbackQueryHandler(view_links, pattern='^show_links$'),
                CallbackQueryHandler(handle_organ_selection, pattern='^select_organ:.*$'),
                # Обработка нажатия кнопки "Добавить лекарство"
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)  # Обработка любого текстового сообщения
            ],
            TYPING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
            TYPING_quantity: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_quantity)],
            TYPING_ORGAN_GROUP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ORGAN),
                # MessageHandler(filters.Regex("^Пропустить$"), skip_current_step),  # Обработка кнопки "Пропустить"
            ],
            TYPING_DISEASE_GROUP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_DISEASE_GROUP),
                # MessageHandler(filters.Regex("^Пропустить$"), skip_current_step),  # Обработка кнопки "Пропустить"
            ],
            TYPING_EXPIRY_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_expiry)],
            TYPING_HTML_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_html_link)],
            SAVE_RECORD_IN_DB: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_save_record)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Добавляем обработчик к приложению
    application.add_handler(conv_handler)

    # Инициализируем планировщик
    scheduler_kol_tablet = BackgroundScheduler()

    ## планировщик для напоминания о нехватки лекарств
    # Настроим планировщик для выполнения функции ежедневно в 12:00
    scheduler_kol_tablet.add_job(run_check_medicines, 'cron', hour='12-22', minute='*')
    scheduler_kol_tablet.add_job(run_check_medicines, 'cron', hour=23, minute='0-30')

    # Запуск планировщика в отдельном потоке
    scheduler_thread = threading.Thread(target=scheduler_kol_tablet.start)
    scheduler_thread.start()

    # Важно: добавьте shutdown планировщика при завершении работы приложения
    atexit.register(lambda: scheduler_kol_tablet.shutdown())

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
