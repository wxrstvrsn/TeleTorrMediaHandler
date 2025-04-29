# downloader.py

import os
import subprocess
from config import DOWNLOAD_DIR
from processor import process_videos

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

async def download_magnet(magnet_link, context):
    download_cmd = [
        "aria2c", magnet_link,
        "--dir=" + DOWNLOAD_DIR,
        "--seed-time=0",
        "--bt-save-metadata=true",
        "--follow-torrent=mem",
        "--max-concurrent-downloads=5",
        "--split=5",
        "--allow-overwrite=true",
    ]

    process = subprocess.run(download_cmd)
    if process.returncode != 0:
        await context.bot.send_message(chat_id=context._chat_id, text="Ошибка при скачивании.")
        return
    await process_videos(context)