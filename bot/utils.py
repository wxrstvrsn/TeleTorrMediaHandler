# utils.py
import asyncio
import os
import subprocess
import json
import logging

# Настройка логгера
logger = logging.getLogger("processor")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)-7s | %(name)s | %(message)s", "%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)

# создаем папку если ее еще нет
def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


# находим данные файла
def get_video_info(path: str) -> dict:
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "format=duration,size,bit_rate",
                "-of", "json",
                path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        info = json.loads(result.stdout)
        duration_str = info["format"].get("duration")
        size_str = info["format"].get("size")
        bitrate_str = info["format"].get("bit_rate")

        if not duration_str or duration_str == "N/A":
            raise ValueError("duration is not available")
        if not size_str or size_str == "N/A":
            raise ValueError("size is not available")

        return {
            "duration": float(duration_str),
            "size": int(size_str),
            "bitrate": int(bitrate_str) if bitrate_str and bitrate_str != "N/A" else None
        }
    except Exception as e:
        logger.error(f"[ffprobe] Не удалось получить инфо о видео: {e}")
        raise


async def run_ffmpeg(cmd: list[str]) -> bool:
    """Асинхронный запуск ffmpeg с выводом в лог"""
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )

        assert process.stdout
        async for line in process.stdout:
            decoded = line.decode(errors="ignore").strip()
            if decoded:
                logger.info(f"[ffmpeg] {decoded}")

        return await process.wait() == 0

    except Exception as e:
        logger.error(f"[ffmpeg] Ошибка при выполнении команды: {e}")
        return False