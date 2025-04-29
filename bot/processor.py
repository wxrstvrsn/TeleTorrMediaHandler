# processor.py

import os
import subprocess
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
            await upload_to_telegram(file, filename, context)
            os.remove(file)
        else:
            await split_by_size_and_send(file, base_name, context)
            os.remove(file)


async def split_by_size_and_send(input_file, base_name, context):
    duration = get_video_duration(input_file)
    if duration is None:
        await context.bot.send_message(chat_id=context._chat_id, text=f"Не удалось получить длительность файла: {input_file}")
        return

    total_size = os.path.getsize(input_file)
    part_size_bytes = MAX_FILESIZE_MB * 1024 * 1024
    num_parts = int(total_size / part_size_bytes) + 1
    part_duration = duration / num_parts

    for i in range(num_parts):
        start_time = i * part_duration
        output_filename = f"{base_name}_part{i+1:03d}.mp4"
        output_path = os.path.join(TEMP_DIR, output_filename)
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(int(start_time)),
            "-t", str(int(part_duration)),
            "-i", input_file,
            "-c", "copy",
            output_path
        ]
        subprocess.run(cmd, check=True)
        if not os.path.exists(output_path) or os.path.getsize(output_path) < 100 * 1024:
            print(f"Ошибка: файл {output_filename} не был создан корректно. Пропускаем отправку.")
            continue

        await upload_to_telegram(output_path, output_filename, context)
        os.remove(output_path)