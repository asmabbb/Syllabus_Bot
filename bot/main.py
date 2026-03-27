from bot.bot_instance import bot
from bot.handlers import start
from bot.handlers.admin_panel import register_admin_panel
from bot.handlers.syllabus import register_syllabus
from bot.handlers.share import register_share_handlers
from bot.database.db import init_db

from flask import Flask
import threading
import os
import time

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

@app.route('/')
def home():
    return "OK", 200

@app.route('/health')
def health():
    return "healthy", 200


# -------------------------
# BOT RUNNER (AUTO-RECOVER)
# -------------------------
def run_bot():
    print("Bot polling started...")

    while True:
        try:
            bot.infinity_polling(
                timeout=60,
                long_polling_timeout=60
            )
        except Exception as e:
            print(f"[ERROR] Bot crashed: {e}")
            time.sleep(5)  # prevent rapid crash loop


# -------------------------
# MAIN ENTRY
# -------------------------
if __name__ == "__main__":
    init_db()

    # Start bot in BACKGROUND (daemon = auto kill with app)
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    print("Flask server starting...")

    # Start Flask (Render requires this)
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get("PORT", 10000))
    )