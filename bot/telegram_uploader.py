# telegram_uploader.py

import os
from config import CHANNEL_ID

async def upload_to_telegram(file_path, display_name, context):
    with open(file_path, 'rb') as f:
        await context.bot.send_document(chat_id=CHANNEL_ID, document=f, caption=display_name)
    os.remove(file_path)