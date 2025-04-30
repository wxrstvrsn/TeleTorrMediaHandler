# processor.py
# ------------
import os
import math
import subprocess
import logging
from config import PROCESSED_DIR
from utils import ensure_dir

logger = logging.getLogger(__name__)


def split_video(input_path: str, max_part_size: int = 2 * 1024 ** 3) -> list:
    """
    Разбивает видео на части не более max_part_size байт,
    выводит прогресс преобразования ffmpeg в консоль.
    Возвращает список путей к .mp4
    """
    ensure_dir(PROCESSED_DIR)
    total = os.path.getsize(input_path)
    parts = math.ceil(total / max_part_size)
    basename = os.path.splitext(os.path.basename(input_path))[0]
    outputs = []

    for i in range(parts):
        start_offset = i * max_part_size
        out_file = os.path.join(PROCESSED_DIR, f"{basename}_part{i + 1:03d}.mp4")
        cmd = [
            'ffmpeg',
            '-y',
            '-ss', str(start_offset),
            '-i', input_path,
            '-c', 'copy',
            '-fs', str(max_part_size),
            '-progress', 'pipe:1',
            '-nostats',
            out_file
        ]
        logger.info(f"[processor] Часть {i + 1}/{parts}: запуск ffmpeg")
        # Запуск ffmpeg и вывод прогресса
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        assert process.stdout is not None
        for line in process.stdout:
            text = line.strip()
            if text:
                # Вывод ключевых метрик из ffmpeg-progress
                logger.info(f"[processor] {text}")
        retcode = process.wait()
        if retcode != 0:
            logger.error(f"[processor] ffmpeg завершился с кодом {retcode}")
            raise RuntimeError(f"ffmpeg вернул ошибку {retcode}")
        logger.info(f"[processor] Часть {i + 1} сохранена: {out_file}")
        outputs.append(out_file)

    return outputs
