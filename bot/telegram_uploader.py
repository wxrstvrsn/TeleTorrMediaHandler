# telegram_uploader.py
# ------------
import asyncio
from telethon import TelegramClient
from config import API_ID, API_HASH, SESSION_NAME, CHAT_ID


def get_client() -> TelegramClient:
    """
    Инициализирует и возвращает клиент Telethon.
    """
    return TelegramClient(SESSION_NAME, API_ID, API_HASH)


async def send_video_files(client: TelegramClient, files: list[str]):
    """
    Отправляет список видео файлов в CHAT_ID с поддержкой стриминга.
    """
    for f in files:
        print(f"[uploader] Отправка {f}")
        await client.send_file(
            CHAT_ID,
            f,
            supports_streaming=True,
            progress_callback=lambda sent, total: print(f"[uploader] {sent*100/total:.1f}%")
        )
        await asyncio.sleep(1)