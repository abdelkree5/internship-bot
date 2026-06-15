import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CV_PDF_PATH = os.getenv("CV_PDF_PATH", "cv.pdf")

DB_PATH = os.path.join(os.path.dirname(__file__), "database", "applications.db")
LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")

os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
