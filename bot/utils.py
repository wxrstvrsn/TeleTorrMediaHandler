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