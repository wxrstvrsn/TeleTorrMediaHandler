# downloader.py

import os
import asyncio
import logging
from config import DOWNLOAD_DIR
from utils import ensure_dir

logger = logging.getLogger(__name__)


async def download_torrent(source: str) -> str:
    """
    Скачивает торрент через aria2c, выводя прогресс в консоль.
    """
    ensure_dir(DOWNLOAD_DIR)

    # Формируем команду с нужными флагами
    cmd = [
        "aria2c",
        f"--dir={DOWNLOAD_DIR}",
        "--seed-time=0",
        "--bt-save-metadata=true",
        "--follow-torrent=mem",
        "--console-log-level=info",  # уровень логов – показываем прогресс
        "--enable-color=false",  # отключаем цветные коды
        source
    ]
    logger.info(f"[downloader] Запуск aria2c: {' '.join(cmd)}")

    # Запускаем процесс и читаем STDOUT построчно
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )
    assert proc.stdout
    while True:
        line = await proc.stdout.readline()
        if not line:
            break
        text = line.decode("utf-8", errors="ignore").rstrip()
        if not text:
            continue
        # Фильтр: убираем низкоуровневые CUID# и piece/request логгинг
        if 'CUID#' in text or 'piece index' in text or 'request index' in text:
            continue
        logger.info(f"[downloader] {text}")

    code = await proc.wait()
    if code != 0:
        logger.error(f"[downloader] aria2c завершился с кодом {code}")
        raise RuntimeError(f"aria2c вернул ошибку {code}")

    # Поиск всех видеофайлов, включая вложенные
    video_files = []
    for root, _, files in os.walk(DOWNLOAD_DIR):
        for file in files:
            if file.lower().endswith(('.mp4', '.mkv', '.avi')):
                full_path = os.path.join(root, file)
                video_files.append(full_path)

    if not video_files:
        logger.error("[downloader] Не найден видеофайл после загрузки")
        raise FileNotFoundError("Видео не найдено в папке загрузки")


    return video_files
