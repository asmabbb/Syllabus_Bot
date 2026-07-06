import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Database connection URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Owner Telegram ID
OWNER_ID = int(os.getenv("OWNER_ID", "0")) # Default to 0 if not set