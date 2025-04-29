#!/data/data/com.termux/files/usr/bin/bash
pkg update -y && pkg upgrade -y
pkg install -y python aria2 ffmpeg git
pip install -r requirements.txt
termux-wake-lock
echo "Запуск бота..."
python bot.py