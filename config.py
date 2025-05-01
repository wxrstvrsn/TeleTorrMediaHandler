# config.py
# ------------
import os
from dotenv import load_dotenv

# Загружаем переменные окружения (API_ID, API_HASH, SESSION_NAME, CHAT_ID)
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_NAME = os.getenv("SESSION_NAME")
# ID вашего канала для публикации (int)
CHAT_ID = int(os.getenv("CHAT_ID"))

# Папки для хранения
DOWNLOAD_DIR = "downloads"
PROCESSED_DIR = "processed"

# Параметры задержек для снижения риска спама
# Секунд между отправками частей видео
UPLOAD_DELAY_SECONDS = 10

# Включение / выключение загрузки в тг
ENABLE_UPLOAD = os.getenv("ENABLE_UPLOAD")

MAX_FILESIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB"))

IS_CONVERTING = False