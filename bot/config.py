# config.py
import os
from dotenv import load_dotenv
# ------------
load_dotenv()
# Конфигурация Telethon и пути
API_ID = os.getenv("API_ID")  # замените на ваш API_ID
API_HASH = os.getenv("API_HASH")
SESSION_NAME = os.getenv("SESSION_NAME")
# Чат (или канал), куда будете отправлять видео
# Можно получить chat_id из @get_id_bot или Telethon
CHAT_ID = os.getenv("CHAT_ID")

# Папки для хранения загрузок и обработанных файлов
DOWNLOAD_DIR = "downloads"
PROCESSED_DIR = "processed"