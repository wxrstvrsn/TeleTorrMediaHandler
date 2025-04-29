
import os

def is_video_file(file_path):
    video_extensions = ['.mp4', '.mkv', '.avi', '.mov']
    return os.path.splitext(file_path)[1].lower() in video_extensions

def get_files_recursive(directory):
    all_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            all_files.append(os.path.join(root, file))
    return all_files

def get_video_duration(file_path):
    import subprocess
    try:
        result = subprocess.run(
            [
                'ffprobe', '-v', 'error', '-show_entries',
                'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
                file_path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return float(result.stdout.strip())
    except Exception:
        return None

async def log(context, message):
    print(message)
