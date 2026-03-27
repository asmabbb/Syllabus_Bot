# set_webhook.py
from bot.bot_instance import bot
import os

RENDER_URL = os.environ.get("RENDER_URL")  # e.g., https://your-app-name.onrender.com
BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot.remove_webhook()
bot.set_webhook(url=f"{RENDER_URL}/{BOT_TOKEN}")
print("Webhook set!")