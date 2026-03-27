# bot/main.py
from bot.bot_instance import bot
from bot.handlers import start
from bot.handlers.admin_panel import register_admin_panel
from bot.handlers.syllabus import register_syllabus
from bot.handlers.share import register_share_handlers
from bot.database.db import init_db

from flask import Flask, request
import os

# -------------------------
# REGISTER HANDLERS
# -------------------------
register_share_handlers(bot)
register_admin_panel(bot)
register_syllabus(bot)

# -------------------------
# FLASK APP
# -------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "CETSU Student Support Bot is alive!"

# Telegram webhook endpoint
@app.route(f"/{os.environ['BOT_TOKEN']}", methods=["POST"])
def telegram_webhook():
    json_update = request.get_json(force=True)
    update = bot.types.Update.de_json(json_update)
    bot.process_new_updates([update])
    return "!", 200

# -------------------------
# INIT DB & SET WEBHOOK
# -------------------------
if __name__ == "__main__":
    init_db()

    # Remove any previous webhook
    bot.remove_webhook()

    # Set new webhook (your Render URL)
    RENDER_URL = os.environ.get("RENDER_URL")  # e.g., https://yourapp.onrender.com
    bot.set_webhook(url=f"{RENDER_URL}/{os.environ['BOT_TOKEN']}")

    print("✅ Webhook set. Bot is ready to receive updates!")