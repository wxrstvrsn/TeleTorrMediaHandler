# bot.py
# ------------
import asyncio
import logging
import random
from telethon import events, errors
import config
from downloader import download_torrent
from processor import split_video
from telegram_uploader import get_client, send_video_files

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s:%(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    client = get_client()

    @client.on(events.NewMessage(pattern=r"https?://.*\\.torrent"))
    async def handler(event):
        link = event.raw_text.strip()
        logger.info(f"Новая ссылка: {link}")
        msg = await event.reply("🔗 Ссылка получена, готовлюсь...")

        try:
            # Загрузка
            await msg.edit("⬇️ Скачиваю торрент, это может занять время...")
            in_file = await download_torrent(link)

            # Обработка
            await msg.edit("⚙️ Конвертирую и разбиваю видео на части...")
            parts = await asyncio.get_event_loop().run_in_executor(None, split_video, in_file)

            # Отправка
            await msg.edit(f"🚀 Начинаю отправку {len(parts)} частей в канал...")
            await send_video_files(client, parts, msg)

            # Завершение
            await msg.edit("✅ Все части успешно отправлены в канал!")
            logger.info("Обработка завершена без ошибок")

        except Exception as e:
            logger.exception("Ошибка в обработчике события")
            try:
                await msg.edit(f"❌ Ошибка: {e}")
            except Exception:
                pass

    logger.info("[bot] Запуск MTProto-бота...")
    await client.start()
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())