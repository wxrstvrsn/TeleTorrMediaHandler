# bot.py

import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from config import BOT_TOKEN
from downloader import download_magnet
import os

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отправь мне magnet-ссылку, и я скачаю и загружу в канал!")

async def handle_magnet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text.strip()
    if not link.startswith("magnet:?"):
        await update.message.reply_text("Это не похоже на magnet-ссылку.")
        return
    await update.message.reply_text("Скачиваю...")
    await download_magnet(link, context)

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_magnet))

if __name__ == '__main__':
    app.run_polling()