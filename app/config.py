import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
SESSION_STRING = os.environ.get("SESSION_STRING", "")

MONGO_URI = os.environ.get("MONGO_URI", "")
DB_NAME = os.environ.get("DB_NAME", "forwarder_bot")

MAIN_CHANNEL = int(os.environ.get("MAIN_CHANNEL", "0"))

ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()]

MAX_FILES_PER_CHANNEL = int(os.environ.get("MAX_FILES_PER_CHANNEL", "2000"))
COPY_DELAY_SECONDS = int(os.environ.get("COPY_DELAY_SECONDS", "10"))
TIMEZONE = os.environ.get("TIMEZONE", "Asia/Kolkata")
