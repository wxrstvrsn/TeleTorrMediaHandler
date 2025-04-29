# processor.py

import os
import subprocess
from config import DOWNLOAD_DIR, TEMP_DIR, MAX_FILESIZE_MB
from telegram_uploader import upload_to_telegram
from utils import is_video_file, get_files_recursive

os.makedirs(TEMP_DIR, exist_ok=True)

async def process_videos(context):
    files = get_files_recursive(DOWNLOAD_DIR)
    for file in files:
        if not is_video_file(file):
            continue
        filename = os.path.basename(file)
        output_dir = os.path.join(TEMP_DIR, filename + "_parts")
        os.makedirs(output_dir, exist_ok=True)

        size_mb = os.path.getsize(file) / (1024 * 1024)
        if file.endswith('.mp4') and size_mb <= MAX_FILESIZE_MB:
            await upload_to_telegram(file, filename, context)
        else:
            output_template = os.path.join(output_dir, filename.replace('.', '_') + "_part%03d.mp4")
            ffmpeg_cmd = [
                "ffmpeg", "-i", file,
                "-c", "copy",
                "-map", "0",
                "-f", "segment",
                "-segment_size", str(MAX_FILESIZE_MB * 1024 * 1024),
                output_template
            ]
            subprocess.run(ffmpeg_cmd, check=True)
            for part in sorted(os.listdir(output_dir)):
                await upload_to_telegram(os.path.join(output_dir, part), part, context)
        os.remove(file)