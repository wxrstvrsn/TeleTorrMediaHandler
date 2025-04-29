# config.py

import os
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
MAX_FILESIZE_MB = 1000
DOWNLOAD_DIR = "downloads"
TEMP_DIR = "temp"

# Быстрая проверка
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден. Убедись, что он указан в .env")
