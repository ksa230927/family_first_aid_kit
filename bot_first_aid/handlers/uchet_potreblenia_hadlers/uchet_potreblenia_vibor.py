import os
import django

# Устанавливаем переменную окружения для настроек
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')  # Замените 'myproject.settings' на имя вашего модуля настроек

# Инициализация Django
django.setup()

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram_data.models import TelegramMessage
from asgiref.sync import sync_to_async
from bot_first_aid.globals import REDUCING_QUANTITY, CHOOSING

async def uchet_potreblenia_vibor(update, context):
    print("uchet_potreblenia_vibor")
    # medicine_names = await sync_to_async(list)(TelegramMessage.objects.values_list('medicine_name', flat=True))
    # Создаём кнопки для каждого наименования
    keyboard = [[InlineKeyboardButton("Проверить нехватку/просрочку", callback_data='nechvatka_prosrochka')],
                [InlineKeyboardButton("Добавить/убрать кол-во ", callback_data='uchet_potreblenia')]
                ]
    # Генерируем клавиатуру
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Отправляем сообщение с динамически созданными кнопками
    await update.callback_query.answer()  # Подтверждаем нажатие кнопки
    await update.callback_query.message.reply_text(
        "Сделайте выбор",
        reply_markup=reply_markup
    )
    return CHOOSING

async def uchet_potreblenia_vibor_nazvania(update, context):
    print("uchet_potreblenia_vibor_nazvania")
    medicine_names = await sync_to_async(list)(TelegramMessage.objects.values_list('medicine_name', flat=True))
    # Создаём кнопки для каждого наименования
    keyboard = [[InlineKeyboardButton(name, callback_data=f'medicine:{name}')] for name in medicine_names]
    # Генерируем клавиатуру
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Отправляем сообщение с динамически созданными кнопками
    await update.callback_query.answer()  # Подтверждаем нажатие кнопки
    await update.callback_query.message.reply_text(
        "Выберите лекарство:",
        reply_markup=reply_markup
    )
    return CHOOSING

async def handle_medicine_selection(update, context):
    query = update.callback_query
    medicine_name = query.data.split(':')[1]

    # Сохраняем выбранное лекарство в user_data
    context.user_data['selected_medicine'] = medicine_name
    await query.answer(f"Вы выбрали: {medicine_name}")
    await query.message.reply_text(f"Вы выбрали: {medicine_name}")
    # Спрашиваем у пользователя количество потреблённого лекарства
    await query.message.reply_text(f"Для '{medicine_name}' введите отрицательную величину, если таблетки/дозы потреблены и положительную, если куплены дополнительно и их нужно добавить в учет")

    return REDUCING_QUANTITY

async def handle_quantity_reduction(update, context):
    medicine_name = context.user_data.get('selected_medicine')

    # Получаем количество, введённое пользователем
    try:
        quantity_consumed = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите корректное число.")
        return REDUCING_QUANTITY

    # Обновляем количество в базе данных
    await sync_to_async(update_medicine_quantity)(medicine_name, quantity_consumed)

    await update.message.reply_text(
        f"Количество '{medicine_name}' обновлено на {quantity_consumed} доз/таблеток."
    )

    # Возвращаемся к CHOOSING
    return CHOOSING

def update_medicine_quantity(medicine_name, quantity_consumed):
    # Ищем лекарство и уменьшаем количество
    medicine = TelegramMessage.objects.filter(medicine_name=medicine_name).first()
    if medicine:
        medicine.quantity += quantity_consumed
        medicine.save()

