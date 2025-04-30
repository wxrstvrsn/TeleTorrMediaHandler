# telegram_uploader.py
# ------------
import os
import asyncio
import logging
import random
from telethon import TelegramClient, errors
import config

logger = logging.getLogger(__name__)

def get_client() -> TelegramClient:
    """Инициализирует Telethon-клиент"""
    return TelegramClient(config.SESSION_NAME, config.API_ID, config.API_HASH)

async def send_video_files(client: TelegramClient, files: list[str], msg) -> None:
    """
    Отправляет части видео в канал, обновляя статус в Telegram-чате.
    """
    total = len(files)
    for idx, fpath in enumerate(files, start=1):
        fname = os.path.basename(fpath)
        status = f"📤 Отправка части {idx}/{total}: {fname}"
        logger.info(status)
        await msg.edit(status)
        try:
            await client.send_file(
                config.CHAT_ID,
                fpath,
                supports_streaming=True,
                progress_callback=lambda sent, total_bytes: logger.debug(f"[uploader] {sent}/{total_bytes}"),
            )
            logger.info(f"[uploader] Часть {idx} успешно отправлена")
        except errors.FloodWaitError as e:
            logger.warning(f"FloodWait: сплю {e.seconds}s")
            await asyncio.sleep(e.seconds)
            # после ожидания повторим отправку
            await client.send_file(config.CHAT_ID, fpath, supports_streaming=True)
        except Exception as e:
            logger.error(f"Ошибка отправки части {idx}: {e}")
            await msg.edit(f"❌ Ошибка при отправке части {idx}: {e}")
            continue

        # задержка между отправками
        delay = config.UPLOAD_DELAY_SECONDS + random.uniform(0, 1)
        logger.debug(f"Жду {delay:.1f}s перед следующей частью")
        await asyncio.sleep(delay)
