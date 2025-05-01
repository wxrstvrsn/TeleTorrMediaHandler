import asyncio
import os
import json
import logging
import subprocess

# Настройка логгера
log = logging.getLogger("processor")
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)-7s | %(name)s | %(message)s", "%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
log.setLevel(logging.INFO)
log.addHandler(handler)

# создаем папку если ее еще нет
def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def get_video_info(path: str) -> dict:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_format", "-show_streams",
        "-print_format", "json",
        path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")

    try:
        info = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError("Failed to parse ffprobe output as JSON")

    if 'format' not in info or 'duration' not in info['format']:
        raise RuntimeError("ffprobe output missing 'format.duration'")

    return info



async def run_ffmpeg(cmd: list[str]) -> bool:
    """Асинхронно запускает ffmpeg и выводит лог построчно"""
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )

    assert process.stdout
    async for line in process.stdout:
        decoded = line.decode(errors='ignore').strip()
        if decoded:
            log.info(f"[ffmpeg] {decoded}")

    return await process.wait() == 0
