import os
import subprocess
import asyncio
from config import DOWNLOAD_DIR, TEMP_DIR, MAX_FILESIZE_MB
from telegram_uploader import upload_to_telegram
from utils import is_video_file, get_files_recursive, get_video_duration, log

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
            try:
                os.remove(file)
            except PermissionError as e:
                await log(context, f"⚠️ Не удалось удалить файл (занят): {file} — {e}")
        else:
            await log(context, f"🎬 Обработка видео: {filename}")
            await split_by_size_and_send(file, base_name, context)
            try:
                os.remove(file)
            except PermissionError as e:
                await log(context, f"⚠️ Не удалось удалить файл (занят): {file} — {e}")

async def split_by_size_and_send(input_file, base_name, context):
    duration = get_video_duration(input_file)
    if duration is None or duration <= 0:
        await log(context, f"❌ Невалидная длительность видео: {input_file}")
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
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            output_path
        ]

        try:
            await log(context, f"🎞️ ffmpeg (copy): {output_filename}")
            proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)

            async for line in proc.stdout:
                decoded = line.decode('utf-8', errors='replace').strip()
                if decoded:
                    print(f"[ffmpeg] {decoded}")

            await proc.wait()

            if not os.path.exists(output_path):
                await log(context, f"❌ ffmpeg не создал файл: {output_filename}")
                continue

            size = os.path.getsize(output_path) / (1024 * 1024)
            await log(context, f"📁 Файл создан: {output_path}, размер: {size:.2f} MB")
            await log(context, f"📤 Попытка отправки: {output_filename}")
            await upload_to_telegram(output_path, output_filename, context)
            await log(context, f"✅ Отправка завершена: {output_filename}")
            try:
                os.remove(output_path)
            except PermissionError as e:
                await log(context, f"⚠️ Не удалось удалить файл (занят): {output_path} — {e}")
        except Exception as e:
            await log(context, f"⚠️ Ошибка обработки {output_filename}: {e}")