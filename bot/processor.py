import os
import math
import asyncio
from typing import Optional
from config import PROCESSED_DIR, MAX_FILESIZE_MB
from utils import get_video_info, run_ffmpeg, log, ensure_dir

# Размер части в байтах (1812 MiB — чуть меньше лимита Telegram)
MAX_PART_BYTES = MAX_FILESIZE_MB * 1024 * 1024


async def split_video(input_path: str) -> list[str]:
    info = await get_video_info(input_path)
    duration = info["duration"]
    video_bitrate = info["video_bitrate"]
    audio_bitrate = info["audio_bitrate"]

    log.info(f"[split] Длительность: {duration:.2f} сек")
    log.info(f"[split] Битрейт видео: {video_bitrate} кбит/с, аудио: {audio_bitrate} кбит/с")

    # Предсказание размера после перекодирования (в байтах)
    total_bitrate_kbps = video_bitrate + audio_bitrate
    estimated_size_bytes = (total_bitrate_kbps * 1000 / 8) * duration

    parts_count = max(1, math.ceil(estimated_size_bytes / MAX_PART_BYTES))
    part_duration = duration / parts_count

    log.info(f"[split] Предсказанный размер файла: {estimated_size_bytes / (1024 ** 2):.2f} MiB")
    log.info(f"[split] Предполагаемое количество частей: {parts_count} (~{part_duration:.2f} сек каждая)")

    filenames = []
    for i in range(parts_count):
        start = int(part_duration * i)
        is_last = (i == parts_count - 1)
        duration_arg = None if is_last else int(part_duration)

        output_path = os.path.join(
            PROCESSED_DIR,
            f"{os.path.basename(input_path).rsplit('.', 1)[0]}_part{i+1:03}.mp4"
        )

        log.info(f"[ffmpeg] 🎞️ Старт перекодировки: part #{i+1}")
        success = await recode_video(
            input_path=input_path,
            output_path=output_path,
            start=start,
            duration=duration_arg
        )

        if success:
            filenames.append(output_path)
            size = os.path.getsize(output_path) / (1024 ** 2)
            log.info(f"[split] ✅ Создан файл: {output_path} ({size:.2f} MiB)")
        else:
            log.error(f"[split] ❌ Ошибка при обработке part #{i+1}")
            break

    return filenames


async def recode_video(input_path: str, output_path: str, start: int = 0, duration: Optional[int] = None) -> bool:
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
    ]

    if duration:
        cmd += ["-t", str(duration)]

    cmd += [output_path]

    return await run_ffmpeg(cmd)
