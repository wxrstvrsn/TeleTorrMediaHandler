import os
import math
from typing import List
from config import PROCESSED_DIR, MAX_FILESIZE_MB
from utils import get_video_info, run_ffmpeg, logger, ensure_dir


async def split_video(input_path: str) -> List[str]:
    ensure_dir(PROCESSED_DIR)

    video_info = get_video_info(input_path)
    if not video_info:
        raise RuntimeError("Не удалось получить информацию о видео")


    duration = video_info["duration"]
    filename_wo_ext = os.path.splitext(os.path.basename(input_path))[0]
    full_recode_path = os.path.join(PROCESSED_DIR, f"{filename_wo_ext}_full_recode.mp4")

    # Перекодировка полного файла
    logger.info("[recode] Перекодировка полного файла...")
    recode_cmd = [
        "ffmpeg", "-y",
        "-stats", "-stats_period", "0.5",
        "-i", input_path,
        "-c:v", "libx264",
        "-preset", "ultrafast", # medium
        "-crf", "23", # 18
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        full_recode_path
    ]

    success = await run_ffmpeg(recode_cmd)
    if not success or not os.path.exists(full_recode_path):
        raise RuntimeError("Ошибка при полной перекодировке")

    # Получаем размер перекодированного файла
    final_size_bytes = os.path.getsize(full_recode_path)
    max_filesize_bytes = MAX_FILESIZE_MB * 1024 * 1024

    # Определяем количество частей
    parts_count = max(1, math.ceil(final_size_bytes / max_filesize_bytes))
    duration_per_part = duration / parts_count
    logger.info(f"[split] Итоговый размер: {final_size_bytes / (1024**2):.2f} МБ — частей: {parts_count} (~{duration_per_part:.2f} сек каждая)")

    output_paths = []

    for i in range(parts_count):
        start = duration_per_part * i
        output_path = os.path.join(PROCESSED_DIR, f"{filename_wo_ext}_part{i + 1:03}.mp4")
        logger.info(f"[ffmpeg] 🎞️ Нарезка part #{i + 1}")

        cmd = [
            "ffmpeg", "-y",
            "-stats", "-stats_period", "0.5",
            "-ss", str(start),
            "-i", full_recode_path,
            "-t", str(duration_per_part),
            "-c", "copy",
            output_path
        ]

        success = await run_ffmpeg(cmd)
        if not success:
            raise RuntimeError(f"[ffmpeg] Ошибка при нарезке part #{i + 1}")

        output_paths.append(output_path)

    return output_paths
