import asyncio
from bot_first_aid.handlers.check_bad_medicines.check_medicines import check_medicines

def run_check_medicines():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(check_medicines())

# # Исправление для планировщика
# import asyncio
# from bot_first_aid.handlers.check_bad_medicines.check_medicines import check_medicines
#
# def run_check_medicines():
#     # Создаем новый цикл событий для асинхронной задачи
#     loop = asyncio.get_event_loop()
#     loop.create_task(check_medicines())  # Запуск асинхронной задачи