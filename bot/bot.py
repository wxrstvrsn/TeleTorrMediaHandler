# bot.py
# ------------
import asyncio
from telethon import events
from downloader import download_torrent
from processor import split_video
from telegram_uploader import get_client, send_video_files


async def main():
    client = get_client()

    @client.on(events.NewMessage(pattern=r"https?://.*\\.torrent"))
    async def handler(event):
        link = event.raw_text.strip()
        msg = await event.reply("🔄 Начинаю загрузку...")

        loop = asyncio.get_event_loop()
        try:
            in_file = await download_torrent(link)
            await msg.edit("⚙️ Обработка видео (разбиение на части)...")
            parts = await loop.run_in_executor(None, split_video, in_file)
            await msg.edit(f"🚀 Отправка {len(parts)} частей...")
            await send_video_files(client, parts)
            await msg.edit("✅ Готово!")
        except Exception as e:
            await msg.edit(f"❌ Ошибка: {e}")

    print("[bot] Запуск MTProto-бота...")
    await client.start()
    await client.run_until_disconnected()


if __name__ == '__main__':
    asyncio.run(main())