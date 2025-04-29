# telegram_uploader.py

import os
import asyncio
from config import CHANNEL_ID
from telegram.error import NetworkError

async def upload_to_telegram(file_path, display_name, context):
    if not os.path.exists(file_path):
        await log(context, f"❌ Файл не найден: {file_path}")
        return

    if os.path.getsize(file_path) < 100 * 1024:  # Меньше 100КБ — подозрительно
        await log(context, f"❌ Файл слишком мал или повреждён: {file_path}")
        return

    retries = 3
    for attempt in range(1, retries + 1):
        try:
            with open(file_path, 'rb') as f:
                await context.bot.send_document(chat_id=CHANNEL_ID, document=f, caption=display_name)
            await log(context, f"✅ Отправлено: {display_name}")
            break
        except NetworkError as e:
            await log(context, f"🌐 Ошибка сети (попытка {attempt}/{retries}) при отправке {display_name}: {e}")
            await asyncio.sleep(5)
        except Exception as e:
            await log(context, f"❌ Ошибка отправки {display_name}: {e}")
            break

    await asyncio.sleep(3)  # Пауза между отправками


async def log(context, message):
    print(message)
    try:
        await context.bot.send_message(chat_id=context._chat_id, text=message)
    except:
        pass