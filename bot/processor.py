# processor.py
# ------------
import os
import math
import subprocess
from config import PROCESSED_DIR
from utils import ensure_dir


def split_video(input_path: str, max_part_size: int = 2 * 1024**3) -> list:
    """
    Разбивает видео на части не более max_part_size байт.
    Возвращает список путей к полученным .mp4
    """
    ensure_dir(PROCESSED_DIR)
    total = os.path.getsize(input_path)
    parts = math.ceil(total / max_part_size)
    basename = os.path.splitext(os.path.basename(input_path))[0]
    outputs = []

    for i in range(parts):
        start_offset = i * max_part_size
        out_file = os.path.join(
            PROCESSED_DIR, f"{basename}_part{i+1:03d}.mp4"
        )
        cmd = [
            'ffmpeg', '-y',
            '-ss', str(start_offset),
            '-i', input_path,
            '-c', 'copy',
            '-fs', str(max_part_size),
            out_file
        ]
        print(f"[processor] Запуск ffmpeg для части {i+1}/{parts}")
        subprocess.check_call(cmd)
        outputs.append(out_file)

    return outputs