import os
import math
from typing import List
from config import PROCESSED_DIR, MAX_FILESIZE_MB
from utils import get_video_info, run_ffmpeg, logger, ensure_dir


async def split_video(input_path: str) -> List[str]:
    ensure_dir(PROCESSED_DIR)
    """Режет видео на части на основе оценки итогового размера после перекодировки"""
    video_info = get_video_info(input_path)
    if not video_info:
        raise RuntimeError("Не удалось получить информацию о видео")

    duration = video_info["duration"]
    bitrate = video_info["bitrate"]  # в кбит/с

    # Предсказанный размер итогового перекодированного файла
    predicted_size_mib = (bitrate * duration) / 8 / 1024  # Kbps → KB → MB

    # Кол-во частей
    estimated_parts = max(1, math.ceil(predicted_size_mib / MAX_FILESIZE_MB))
    duration_per_part = duration / estimated_parts

    logger.info(f"[split] Длительность: {duration:.2f} сек — частей: {estimated_parts} (~{duration_per_part:.2f} сек каждая)")

    filename_wo_ext = os.path.splitext(os.path.basename(input_path))[0]
    output_paths = []

    for i in range(estimated_parts):
        start = duration_per_part * i
        output_path = os.path.join(PROCESSED_DIR, f"{filename_wo_ext}_part{i + 1:03}.mp4")
        logger.info(f"[ffmpeg] 🎞️ Старт перекодировки: part #{i + 1}")

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-i", input_path,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            "-t", str(duration_per_part),
            output_path
        ]

        success = await run_ffmpeg(cmd)
        if not success:
            raise RuntimeError(f"[ffmpeg] Ошибка при обработке part #{i + 1}")

        output_paths.append(output_path)

    return output_paths
