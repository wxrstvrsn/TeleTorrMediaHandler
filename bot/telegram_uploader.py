# telegram_uploader.py

import os
import asyncio
from config import CHANNEL_ID
from telegram.error import NetworkError

async def upload_to_telegram(file_path, display_name, context):
    if not os.path.exists(file_path):
        print(f"Файл {file_path} не найден. Пропускаем отправку.")
        return

    if os.path.getsize(file_path) < 100 * 1024:  # Файл меньше 100 КБ — подозрительно
        print(f"Файл {file_path} слишком маленький. Пропускаем отправку.")
        return

    retries = 3
    for attempt in range(retries):
        try:
            with open(file_path, 'rb') as f:
                await context.bot.send_document(chat_id=CHANNEL_ID, document=f, caption=display_name)
            print(f"Файл успешно отправлен: {display_name}")
            break  # если успех — выходим из цикла
        except NetworkError as e:
            print(f"Ошибка сети при отправке {display_name} (попытка {attempt+1}/{retries}): {e}")
            await asyncio.sleep(5)  # ждем 5 секунд перед новой попыткой
        except Exception as e:
            print(f"Неизвестная ошибка при отправке {display_name}: {e}")
            break

    await asyncio.sleep(3)  # Пауза 3 секунды после успешной отправки
