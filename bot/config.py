import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Database connection URL
DATABASE_URL = os.getenv("DATABASE_URL")

# List of sub-admin Telegram IDs
ADMINS = list(map(int, os.getenv("ADMINS", "").split(","))) if os.getenv("ADMINS") else []

# List of super-admin Telegram IDs
SUPER_ADMINS = list(map(int, os.getenv("SUPER_ADMINS", "").split(","))) if os.getenv("SUPER_ADMINS") else []