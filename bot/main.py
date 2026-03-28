from bot.bot_instance import bot
import telebot

import bot.handlers.start
from bot.handlers.admin_panel import register_admin_panel
from bot.handlers.syllabus import register_syllabus
from bot.handlers.share import register_share_handlers

from bot.database.db import init_db

from flask import Flask, request
import os

# -------------------------
# CONFIG
# -------------------------
TOKEN = os.environ.get("BOT_TOKEN")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")  # IMPORTANT

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
    return "Bot is alive (webhook mode)"

# 🔥 THIS IS THE IMPORTANT ROUTE
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200


# -------------------------
# STARTUP
# -------------------------
if __name__ == "__main__":
    init_db()

    print("Setting webhook...")

    bot.remove_webhook()

    webhook_url = f"{RENDER_URL}/{TOKEN}"

    print("Webhook URL:", webhook_url)

    bot.set_webhook(url=webhook_url)

    print("Webhook set successfully!")

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))