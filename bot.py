import os
import django
from dotenv import load_dotenv

# Устанавливаем настройки Django до импорта моделей
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telegram_project.settings')

# Инициализация Django
django.setup()

from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters
from telegram.ext.filters import TEXT, COMMAND, Regex
from django.conf import settings
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import threading
from bot_first_aid.handlers import *
from bot_first_aid.handlers.uchet_potreblenia_hadlers.uchet_potreblenia_vibor import uchet_potreblenia_vibor_nazvania, handle_medicine_selection, handle_quantity_reduction, uchet_potreblenia_vibor
from bot_first_aid.globals import CHOOSING, TYPING_NAME, TYPING_EXPIRY_DATE, TYPING_DISEASE_GROUP, \
    TYPING_ORGAN_GROUP, SAVE_RECORD_IN_DB, TYPING_HTML_LINK, TYPING_quantity, REDUCING_QUANTITY

# Инициализируем планировщик
scheduler = BackgroundScheduler()

# Загружаем переменные из .env файла
load_dotenv()

# функция пока не задейсвована (сейчас она аналогична cancel_input)
# async def handle_q_cancel(update, context):
#     print("handle_q_cancel")
#     # Если пользователь вводит "q", выполняем cancel_input
#     if update.message.text.lower() == 'q':
#         await cancel_input(update, context)  # Вызываем функцию отмены
#         return ConversationHandler.END

# Вспомогательная функция для создания списка обработчиков
def create_state_handlers(main_handler):
    return [
        MessageHandler(TEXT & Regex('^(q|й)$'), cancel_input),  # Обработчик отмены на "q"
        MessageHandler(TEXT & ~COMMAND, main_handler)       # Основной обработчик состояния
    ]

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
                CallbackQueryHandler(uchet_potreblenia_vibor, pattern='^uchet_potreblenia_vibor'),
                CallbackQueryHandler(uchet_potreblenia_vibor_nazvania, pattern='^uchet_potreblenia'),
                CallbackQueryHandler(check_medicines, pattern='^nechvatka_prosrochka'),
                CallbackQueryHandler(handle_organ_selection, pattern='^select_organ:.*$'),
                CallbackQueryHandler(handle_medicine_selection, pattern='^medicine:.*$'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)  # Обработка любого текстового сообщения
            ],
            REDUCING_QUANTITY: create_state_handlers(handle_quantity_reduction),
            TYPING_NAME: create_state_handlers(handle_name),
            TYPING_quantity: create_state_handlers(handle_quantity),
            TYPING_ORGAN_GROUP: create_state_handlers(handle_ORGAN),
            TYPING_DISEASE_GROUP: create_state_handlers(handle_DISEASE_GROUP),
            TYPING_EXPIRY_DATE: create_state_handlers(handle_expiry),
            TYPING_HTML_LINK: create_state_handlers(handle_html_link),
            SAVE_RECORD_IN_DB: create_state_handlers(handle_save_record)
        },
        fallbacks=[
            CommandHandler('cancel', cancel_input),
            MessageHandler(filters.TEXT & filters.Regex('^q$'), cancel_input)
        ],
    )

    # Добавляем обработчик к приложению
    application.add_handler(conv_handler)

    # Инициализируем планировщик
    scheduler_kol_tablet = BackgroundScheduler()

    ## планировщик для напоминания о нехватки лекарств
    # Настроим планировщик для выполнения функции ежедневно в 12:00
    scheduler_kol_tablet.add_job(run_check_medicines, 'cron', hour='12-22', minute='*')
    scheduler_kol_tablet.add_job(run_check_medicines, 'cron', hour=23, minute='0,10,20,30')

    # Запуск планировщика в отдельном потоке
    scheduler_thread = threading.Thread(target=scheduler_kol_tablet.start)
    scheduler_thread.start()

    # Важно: добавьте shutdown планировщика при завершении работы приложения
    atexit.register(lambda: scheduler_kol_tablet.shutdown())

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
