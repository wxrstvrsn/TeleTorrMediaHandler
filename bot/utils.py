# utils.py

import os
import subprocess
import json
import logging
import signal
import asyncio

logger = logging.getLogger(__name__)

# создаем папку если ее еще нет
def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


# находим длительность
def get_video_duration(path: str) -> float:
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "format=duration",
            "-of", "json",
            path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except Exception as e:
        logger.error(f"[ffprobe] Ошибка при получении длительности: {e}")
        raise

active_processes: list[asyncio.subprocess.Process] = []

def kill_active_processes():
    for process in active_processes:
        if process.returncode is None:
            try:
                process.kill()
                print(f"[cleanup] 🔪 Процесс {process.pid} убит")
            except Exception as e:
                print(f"[cleanup] ❌ Ошибка при убийстве процесса {process.pid}: {e}")
    active_processes.clear()