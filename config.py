import os

BLOCK_APPS = ["steam.exe", "Telegram.exe", "Discord.exe"]
BLOCK_SITES = ["Telegram", "YouTube", "ВКонтакте", "Лента новостей", "Wildberries", "Ozon", "Reddit", "WhatsApp", "Мессенджер"]
CHEK_INTERVAL = 2
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_FILE_PATH = os.path.join(BASE_DIR, "block_page.html")
REDIRECT_URL = f"file:///{HTML_FILE_PATH.replace('\\', '/')}"