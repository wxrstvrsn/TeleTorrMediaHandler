# bot.py
# ------------
import os
import asyncio
import logging
import getpass
from telethon import TelegramClient, events, errors
from telethon.tl.types import DocumentAttributeFilename

import config
from downloader import download_torrent
from processor import split_video
from telegram_uploader import get_client, send_video_files
from utils import ensure_dir

#------------------------

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

# Флаг режима обновления подписей
update_names_mode = False

async def main():
    client = get_client()
    logger.info("Инициализация бота...")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^/start$"))
    async def start_handler(event):
        logger.debug("Получена команда /start")
        await event.reply("✅ Бот активирован! Отправьте ссылку на torrent, magnet или .torrent файл.")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^/updateNames$"))
    async def update_mode_handler(event):
        nonlocal update_names_mode  # noqa: F821
        update_names_mode = True
        logger.info("Режим обновления подписей включен")
        await event.reply("🔄 Режим обновления подписей включён. Новые видео получат подписи по имени файла.")

    @client.on(events.NewMessage(incoming=True, chats=config.CHAT_ID))
    async def update_names_handler(event):
        global update_names_mode
        if not update_names_mode:
            return
        doc = event.message.document
        if not doc:
            return
        # Ищем оригинальное имя файла
        file_name = None
        for attr in doc.attributes:
            if isinstance(attr, DocumentAttributeFilename):
                file_name = attr.file_name
                break
        if not file_name:
            return
        try:
            await client.edit_message(
                entity=config.CHAT_ID,
                message=event.message.id,
                caption=file_name
            )
            logger.info(f"Подпись сообщения {event.message.id} обновлена на: {file_name}")
        except errors.MessageNotModifiedError:
            logger.debug(f"Сообщение {event.message.id} уже имеет необходимую подпись")
        except Exception as e:
            logger.error(f"Ошибка при обновлении подписи: {e}")

    @client.on(events.NewMessage(incoming=True, outgoing=True))
    async def handler(event):
        # Основной функционал: загрузка, обработка, отправка
        text = (event.raw_text or '').strip()
        logger.info("Получено сообщение для обработки")
        link = None
        is_file = False

        # Распознаём магнит, URL или .torrent
        if text.startswith("magnet:"):
            link = text
            logger.debug("Распознан magnet-ссылка")
        elif text.lower().startswith("http") and text.lower().endswith(".torrent"):
            link = text
            logger.debug("Распознан HTTP .torrent URL")
        elif event.message.document:
            for attr in event.message.document.attributes:
                if isinstance(attr, DocumentAttributeFilename) and attr.file_name.lower().endswith(".torrent"):
                    torrent_path = os.path.join(config.DOWNLOAD_DIR, attr.file_name)
                    logger.debug(f"Скачиваем .torrent-файл: {attr.file_name}")
                    ensure_dir(config.DOWNLOAD_DIR)
                    await event.reply("📥 Загружаю .torrent файл...")
                    await client.download_media(event.message, file=torrent_path)
                    link = torrent_path
                    is_file = True
                    break

        if not link:
            logger.debug("Сообщение не распознано как torrent/magnet/file, пропуск")
            return

        # Старт обработки
        await event.reply("🔗 Ссылка получена, начинаю обработку...")
        try:
            # Шаг 1: загрузка
            logger.info("Этап 1/3: загрузка торрента")
            in_file = await download_torrent(link)

            # Шаг 2: конвертация и нарезка
            logger.info("Этап 2/3: конвертация и нарезка видео")
            parts = await asyncio.get_event_loop().run_in_executor(None, split_video, in_file)


            # Шаг 3: отправка
            if config.ENABLE_UPLOAD:
                logger.info(f"Этап 3/3: отправка {len(parts)} частей")
                await send_video_files(client, parts, event)

                logger.info("Обработка завершена успешно")
                await event.reply("✅ Все части видео отправлены")
            else:
                logger.info(f"Этап 3/3: отправка {len(parts)} скоро будет выполнена... \t Следите за обновлениями :P")
        except Exception as e:
            logger.exception("Ошибка в процессе обработки")
            await event.reply(f"❌ Ошибка обработки: {e}")

    # Запуск бота и авторизация
    logger.info("Запуск MTProto-бота...")
    await client.start(
        phone=lambda: input("📲 Введите номер телефона (с +7...): "),
        code_callback=lambda: input("🔑 Введите код из Telegram: "),
        password=lambda: getpass.getpass("🔒 Введите пароль 2FA (или просто Enter): ")
    )
    me = await client.get_me()
    logger.info(f"Бот авторизован как {me.username} (id={me.id})")
    logger.info("Ожидание команд и новых сообщений...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
