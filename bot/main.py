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
# FLASK APP (KEEP ALIVE)
# -------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "CETSU Syllabus Bot is alive!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# -------------------------
# SAFE POLLING LOOP
# -------------------------
import threading

def polling_worker():
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print("Polling crashed:", e)

def start_bot():
    while True:
        t = threading.Thread(target=polling_worker)
        t.start()

        # ⏱️ Force restart every 15 minutes
        time.sleep(900)

        print("Forcing polling restart...")
        bot.stop_polling()
        t.join()
# -------------------------
# START EVERYTHING
# -------------------------
if __name__ == "__main__":
    init_db()

    bot.delete_webhook()
    print("Webhook deleted")

    # Start Flask
    threading.Thread(target=run_web, daemon=True).start()

    # Start Bot (SAFE)
    start_bot()