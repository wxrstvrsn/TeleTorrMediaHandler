# utils.py
# ------------
import os


def ensure_dir(path: str):
    """Создаёт папку, если её нет"""
    os.makedirs(path, exist_ok=True)
