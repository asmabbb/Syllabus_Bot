from bot.bot_instance import bot

from bot.handlers import start
from bot.handlers.admin_panel import register_admin_panel
from bot.handlers.syllabus import register_syllabus

from bot.database.db import init_db


# ----- Flask Server -----
from flask import Flask
import threading
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "📚 CETSU Syllabus Bot is alive!"

def run_web():
    print("Starting bot polling...")
    bot.remove_webhook()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)




# ---- Start Everything ---- 

if __name__ == "__main__":
    init_db()

# Register handlers
    register_admin_panel(bot)
    register_syllabus(bot)

    bot.remove_webhook()
    threading.Thread(target=lambda: bot.infinity_polling()).start()

    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
