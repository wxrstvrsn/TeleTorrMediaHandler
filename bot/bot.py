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
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)-7s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler.setFormatter(formatter)
root_logger.handlers = [console_handler]

logger = logging.getLogger('bot')

async def main():
    client = get_client()
    logger.info("Инициализация бота...")

    # Тестовый хэндлер для /start
    @client.on(events.NewMessage(outgoing=True, pattern=r"^/start$"))
    async def test_handler(event):
        logger.debug("Тестовый хэндлер сработал (/start)")
        await event.reply("✅ Бот активирован! Отправьте ссылку на torrent или magnet.")
        return

    # Основной хэндлер
    @client.on(events.NewMessage(incoming=True, outgoing=True))
    async def handler(event):
        logger.info("Получено сообщение от пользователя")
        link = None
        is_file = False

        txt = (event.raw_text or '').strip()
        # Распознаём источники
        if txt.startswith("magnet:"):
            link = txt
            logger.debug("Распознан magnet-ссылка")
        elif txt.lower().startswith("http") and txt.lower().endswith(".torrent"):
            link = txt
            logger.debug("Распознан HTTP .torrent URL")
        elif event.message.document:
            # Локальный .torrent файл
            for attr in event.message.document.attributes:
                if isinstance(attr, DocumentAttributeFilename) and attr.file_name.lower().endswith(".torrent"):
                    ensure_dir(config.DOWNLOAD_DIR)
                    torrent_path = os.path.join(config.DOWNLOAD_DIR, attr.file_name)
                    logger.debug(f"Загрузка .torrent-файла: {attr.file_name}")
                    await event.reply("📥 Получаю .torrent-файл...")
                    await client.download_media(event.message, file=torrent_path)
                    link = torrent_path
                    is_file = True
                    break

        if not link:
            logger.debug("Источник не распознан, пропуск сообщения")
            return

        source_type = "файл" if is_file else "ссылка"
        logger.info(f"Новый источник ({source_type}): {link}")
        msg = await event.reply("🔗 Ссылка получена, начинаю обработку...")

        try:
            # Этап загрузки
            logger.info("Этап 1/3: загрузка торрента")
            await msg.edit("⬇️ Скачиваю торрент... Это может занять время.")
            in_file = await download_torrent(link)

            # Этап обработки
            logger.info("Этап 2/3: конвертация и разбивка видео")
            await msg.edit("⚙️ Конвертирую и разбиваю видео на части...")
            parts = await asyncio.get_event_loop().run_in_executor(None, split_video, in_file)

            # Этап отправки
            logger.info(f"Этап 3/3: отправка {len(parts)} частей")
            await msg.edit(f"🚀 Начинаю отправку {len(parts)} частей в канал...")
            await send_video_files(client, parts, msg)

            # Завершение
            await msg.edit("✅ Все части успешно отправлены в канал!")
            logger.info("Обработка успешно завершена");
        except Exception as e:
            logger.exception("Ошибка в процессе обработки")
            try:
                await msg.edit(f"❌ Ошибка: {e}")
            except Exception:
                logger.error("Не удалось обновить сообщение об ошибке")

    # Запуск бота
    logger.info("Запуск MTProto-бота...")
    await client.start(
        phone=lambda: input("📲 Введите номер телефона (с +7...): "),
        code_callback=lambda: input("🔑 Введите код из Telegram: "),
        password=lambda: getpass.getpass("🔒 Введите пароль 2FA (или просто Enter): ")
    )
    logger.info("Бот авторизован и готов к работе")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
