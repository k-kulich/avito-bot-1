import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
PROXY = os.getenv("MOBILE_PROXY")
CHANGE_IP = os.getenv("CHANGE_IP")

if not TELEGRAM_TOKEN or not DATABASE_URL or not PROXY:
    raise ValueError("Не заданы обязательные переменные окружения")