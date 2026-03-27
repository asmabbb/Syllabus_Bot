from bot.bot_instance import bot

from bot.handlers import start
from bot.handlers.admin_panel import register_admin_panel
from bot.handlers.syllabus import register_syllabus
from bot.handlers.share import register_share_handlers

from bot.database.db import init_db

from flask import Flask
import threading
import os

# -------------------------
# REGISTER HANDLERS
# -------------------------
register_share_handlers(bot)
register_admin_panel(bot)
register_syllabus(bot)

# -------------------------
# FLASK APP (for uptime monitor)
# -------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "CETSU Syllabus Bot is alive!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# Start web server in a separate thread
threading.Thread(target=run_web).start()

# -------------------------
# INIT DB
# -------------------------
init_db()

# -------------------------
# START BOT POLLING
# -------------------------
print("Bot is ready! Waiting for Telegram updates...")
bot.infinity_polling(timeout=10, long_polling_timeout=5)