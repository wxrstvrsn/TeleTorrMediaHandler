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
def get_video_info(filepath: str) -> dict:
    """Получает длительность и битрейт видео через ffprobe"""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "format=duration:stream=bit_rate",
                "-of", "default=noprint_wrappers=1:nokey=1",
                filepath
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )

        lines = result.stdout.strip().split("\n")

        # Длительность в секундах (строка → float)
        duration = float(lines[0])
        # Битрейт в кбит/с (может быть на второй строке, иногда отсутствует)
        bitrate = int(lines[1]) / 1000 if len(lines) > 1 else 1500  # по умолчанию — 1500 кбит/с

        return {"duration": duration, "bitrate": bitrate}

    except Exception as e:
        logger.error(f"[ffprobe] Не удалось получить инфо о видео: {e}")
        return {}

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