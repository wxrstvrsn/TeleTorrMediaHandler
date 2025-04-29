import os
import asyncio
from config import CHANNEL_ID
from telegram.error import NetworkError

async def upload_to_telegram(file_path, display_name, context):
    if not os.path.exists(file_path):
        print(f"❌ Файл не найден: {file_path}")
        return

    if os.path.getsize(file_path) < 100 * 1024:
        print(f"❌ Файл слишком мал или повреждён: {file_path}")
        return

    retries = 3
    for attempt in range(1, retries + 1):
        try:
            with open(file_path, 'rb') as f:
                await context.bot.send_video(
                    chat_id=CHANNEL_ID,
                    video=f,
                    caption=display_name,
                    supports_streaming=True
                )
            print(f"✅ Отправлено: {display_name}")
            break
        except NetworkError as e:
            print(f"🌐 Ошибка сети (попытка {attempt}/{retries}) при отправке {display_name}: {e}")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"❌ Ошибка отправки {display_name}: {e}")
            break
    else:
        print(f"❌ Все попытки отправки {display_name} завершились неудачей.")

    await asyncio.sleep(3)