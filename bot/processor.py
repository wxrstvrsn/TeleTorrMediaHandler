# processor.py

import os
import math
import asyncio
import logging
from config import PROCESSED_DIR, MAX_FILESIZE_MB
from utils import ensure_dir, get_video_duration

logger = logging.getLogger(__name__)


def split_video(input_path: str) -> list[str]:
    ensure_dir(PROCESSED_DIR)

    total_size = os.path.getsize(input_path)
    max_bytes = MAX_FILESIZE_MB * 1024 * 1024

    if total_size <= max_bytes:
        logger.info(f"[split] Файл {input_path} уже меньше {MAX_FILESIZE_MB} МБ, перекодируем целиком")
        return [recode_video(input_path, 0, None, 1)]

    duration = get_video_duration(input_path)
    parts_count = math.ceil(total_size / max_bytes)
    part_duration = duration / parts_count

    logger.info(f"[split] Длительность: {duration:.2f} сек — частей: {parts_count} (~{part_duration:.2f} сек каждая)")

    parts = []
    for i in range(parts_count):
        start = i * part_duration
        out_path = os.path.join(
            PROCESSED_DIR,
            f"{os.path.splitext(os.path.basename(input_path))[0]}_part{i + 1:03}.mp4"
        )
        parts.append(recode_video(input_path, start, part_duration, i + 1, out_path))

    return parts


def recode_video(input_path: str, start: float, duration: float | None, part_num: int, output_path: str = None) -> str:
    if not output_path:
        base = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(PROCESSED_DIR, f"{base}_part{part_num:03}.mp4")

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
    ]

    if duration:
        cmd += ["-t", str(duration)]

    cmd += [
        "-i", input_path,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart"
        "-stats",
        output_path
    ]

    logger.info(f"[ffmpeg] 🎞️ Старт перекодировки: part #{part_num}")
    result = asyncio.run(run_ffmpeg(cmd))
    if not result:
        raise RuntimeError(f"[ffmpeg] Ошибка при обработке part #{part_num}")

    return output_path


async def run_ffmpeg(cmd: list[str]) -> bool:
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )
    assert process.stdout
    async for line in process.stdout:
        logger.info(f"[ffmpeg] {line.decode(errors='ignore').strip()}")

    return await process.wait() == 0
