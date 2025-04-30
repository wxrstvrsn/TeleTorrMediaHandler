# downloader.py
# ------------
import os
import asyncio
from config import DOWNLOAD_DIR
from utils import ensure_dir

async def download_torrent(magnet_link: str) -> str:
    """
    Скачивает торрент через aria2c и возвращает путь к
    самому большому скачанному видео-файлу.
    """
    ensure_dir(DOWNLOAD_DIR)
    cmd = [
        "aria2c",
        f"--dir={DOWNLOAD_DIR}",
        "--seed-time=0",
        "--bt-save-metadata=true",
        "--follow-torrent=mem",
        "--summary-interval=10",
        magnet_link
    ]
    print(f"[downloader] Запуск aria2c: {' '.join(cmd)}")
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"aria2c вернул ошибку: {err.decode().strip()}")

    # После завершения aria2c в DOWNLOAD_DIR появятся файлы
    largest_file = None
    largest_size = 0
    for root, _, files in os.walk(DOWNLOAD_DIR):
        for fname in files:
            path = os.path.join(root, fname)
            size = os.path.getsize(path)
            # учитываем только видеофайлы
            if size > largest_size and path.lower().endswith((".mp4", ".mkv", ".avi")):
                largest_size = size
                largest_file = path

    if not largest_file:
        raise FileNotFoundError("Не найдено скачанного видео-файла")
    print(f"[downloader] Завершено, найден файл: {largest_file}")
    return largest_file