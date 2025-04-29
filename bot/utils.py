# utils.py

import os

def is_video_file(file):
    video_exts = ['.mp4', '.mkv', '.avi', '.mov']
    return any(file.endswith(ext) for ext in video_exts)

def get_files_recursive(directory):
    result = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            result.append(os.path.join(root, file))
    return result
# utils.py (добавить)

import subprocess
import json

def get_video_duration(filepath):
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "json", filepath
        ], capture_output=True, text=True, check=True)
        json_output = json.loads(result.stdout)
        return float(json_output["format"]["duration"])
    except Exception:
        return None