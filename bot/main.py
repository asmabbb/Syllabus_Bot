from bot.bot_instance import bot
from bot.handlers import start
from bot.handlers.admin_panel import register_admin_panel
from bot.handlers.syllabus import register_syllabus
from bot.handlers.share import register_share_handlers
from bot.database.db import init_db

from flask import Flask
import threading
import os

# Register handlers
register_admin_panel(bot)
register_syllabus(bot)
register_share_handlers(bot)


app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive"


def run_bot():
    print("Bot polling started...")
    bot.infinity_polling()


if __name__ == "__main__":
    init_db()

    

    # Start bot in thread
    threading.Thread(target=run_bot).start()

    # Start web server
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))