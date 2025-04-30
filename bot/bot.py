# bot.py
# ------------
import os
import asyncio
import logging
import getpass
from telethon import events
from telethon.tl.types import DocumentAttributeFilename
import config
from downloader import download_torrent
from processor import split_video
from telegram_uploader import get_client, send_video_files
from utils import ensure_dir

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s:%(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    client = get_client()

    @client.on(events.NewMessage(pattern=r"^/start", incoming=True, outgoing=True))
    async def test_handler(event):
        logger.info("Тестовый хэндлер сработал")
        await event.reply("ловушка сработала")
        return

    @client.on(events.NewMessage)
    async def handler(event):
        link = None
        is_file = False
        # поддержка magnet: URI и HTTP .torrent
        if event.raw_text:
            txt = event.raw_text.strip()
            if txt.startswith("magnet:"):
                link = txt
            elif txt.lower().startswith("http") and txt.lower().endswith(".torrent"):
                link = txt
        # поддержка загрузки .torrent-файла
        if not link and event.message.document:
            doc = event.message.document
            fname = None
            for attr in doc.attributes:
                if isinstance(attr, DocumentAttributeFilename):
                    fname = attr.file_name
                    break
            if fname and fname.lower().endswith(".torrent"):
                ensure_dir(config.DOWNLOAD_DIR)
                torrent_path = os.path.join(config.DOWNLOAD_DIR, fname)
                logger.info(f"Скачиваю .torrent файл: {fname}")
                await event.reply("📥 Получаю файл .torrent...")
                await client.download_media(event.message, file=torrent_path)
                link = torrent_path
                is_file = True
        # если источник не опознан — игнорируем сообщение
        if not link:
            return

        source_type = "файл" if is_file else "ссылка"
        logger.info(f"Новый источник ({source_type}): {link}")
        msg = await event.reply("🔗 Ссылка получена, готовлюсь...")

        try:
            # этап загрузки
            await msg.edit("⬇️ Скачиваю торрент, это может занять время...")
            in_file = await download_torrent(link)
            # этап обработки
            await msg.edit("⚙️ Конвертирую и разбиваю видео на части...")
            parts = await asyncio.get_event_loop().run_in_executor(None, split_video, in_file)
            # этап отправки
            await msg.edit(f"🚀 Начинаю отправку {len(parts)} частей в канал...")
            await send_video_files(client, parts, msg)
            # финал
            await msg.edit("✅ Все части успешно отправлены в канал!")
            logger.info("Обработка завершена без ошибок")
        except Exception as e:
            logger.exception("Ошибка в обработчике события")
            try:
                await msg.edit(f"❌ Ошибка: {e}")
            except:
                pass

    logger.info("[bot] Запуск MTProto-бота...")
    await client.start(
        phone=lambda: input("📲 Введите номер телефона (с +7…): "),
        code_callback=lambda: input("🔑 Введите код из Telegram: "),
        password=lambda: getpass.getpass("🔒 Введите пароль 2FA (или просто Enter, если нет): ")
    )
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
