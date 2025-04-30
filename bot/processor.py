# processor.py
# ------------
import os
import math
import subprocess
import logging
from config import PROCESSED_DIR
from utils import ensure_dir

logger = logging.getLogger(__name__)

def split_video(input_path: str, max_part_size: int = 2 * 1024**3) -> list:
    """
    Разбивает видео на части не более max_part_size байт.
    Возвращает список путей к .mp4
    """
    ensure_dir(PROCESSED_DIR)
    total = os.path.getsize(input_path)
    parts = math.ceil(total / max_part_size)
    basename = os.path.splitext(os.path.basename(input_path))[0]
    outputs = []

    for i in range(parts):
        start_offset = i * max_part_size
        out_file = os.path.join(PROCESSED_DIR, f"{basename}_part{i+1:03d}.mp4")
        cmd = [
            'ffmpeg', '-y',
            '-ss', str(start_offset),
            '-i', input_path,
            '-c', 'copy',
            '-fs', str(max_part_size),
            out_file
        ]
        logger.info(f"[processor] Часть {i+1}/{parts}: запуск ffmpeg")
        subprocess.check_call(cmd)
        logger.info(f"[processor] Часть {i+1} сохранена: {out_file}")
        outputs.append(out_file)

    return outputs