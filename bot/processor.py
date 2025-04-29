# processor.py

import os
import subprocess
import asyncio
from config import DOWNLOAD_DIR, TEMP_DIR, MAX_FILESIZE_MB
from telegram_uploader import upload_to_telegram
from utils import is_video_file, get_files_recursive, get_video_duration


async def process_videos(context):
    files = get_files_recursive(DOWNLOAD_DIR)
    for file in files:
        if not is_video_file(file):
            continue

        filename = os.path.basename(file)
        base_name = os.path.splitext(filename)[0]
        temp_output_dir = os.path.join(TEMP_DIR, base_name + "_parts")
        os.makedirs(temp_output_dir, exist_ok=True)

        size_mb = os.path.getsize(file) / (1024 * 1024)
        if file.endswith(".mp4") and size_mb <= MAX_FILESIZE_MB:
            await log(context, f"📦 Отправка: {filename}")
            await upload_to_telegram(file, filename, context)
            os.remove(file)
        else:
            await log(context, f"🎬 Обработка видео: {filename}")
            await split_by_size_and_send(file, base_name, context)
            os.remove(file)


async def split_by_size_and_send(input_file, base_name, context):
    duration = get_video_duration(input_file)
    if duration is None:
        await log(context, f"❌ Не удалось получить длительность: {input_file}")
        return

    total_size = os.path.getsize(input_file)
    part_size_bytes = MAX_FILESIZE_MB * 1024 * 1024
    num_parts = int(total_size / part_size_bytes) + 1
    part_duration = duration / num_parts

    for i in range(num_parts):
        start_time = i * part_duration
        output_filename = f"{base_name}_part{i+1:03d}.mp4"
        output_path = os.path.join(TEMP_DIR, output_filename)

        # 1. Попытка через -c copy
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(int(start_time)),
            "-t", str(int(part_duration)),
            "-i", input_file,
            "-c", "copy",
            output_path
        ]
        try:
            await log(context, f"🎞️ ffmpeg (copy): {output_filename}")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if "pts has no value" in result.stderr or not os.path.exists(output_path):
                raise RuntimeError("⚠️ ffmpeg copy output has no pts or file missing.")

            await log(context, f"📤 Попытка отправки файла: {output_filename}")
            await upload_to_telegram(output_path, output_filename, context)
            await log(context, f"✅ Попытка завершена: {output_filename}")

            os.remove(output_path)
        except Exception as e:
            await log(context, f"⚠️ Ошибка в copy: {e} — перекодируем...")

            cmd = [
                "ffmpeg", "-y",
                "-ss", str(int(start_time)),
                "-t", str(int(part_duration)),
                "-i", input_file,
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                output_path
            ]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                await log(context,
                          f"📁 Файл создан: {output_path}, размер {os.path.getsize(output_path) / (1024 * 1024):.2f} MB")

                if not os.path.exists(output_path):
                    await log(context, f"❌ ffmpeg failed to create {output_filename}")
                    continue
                await upload_to_telegram(output_path, output_filename, context)
                os.remove(output_path)
            except Exception as e2:
                await log(context, f"❌ Полная ошибка ffmpeg: {e2}")


async def log(context, message):
    print(message)
    try:
        await context.bot.send_message(chat_id=context._chat_id, text=message)
    except:
        pass