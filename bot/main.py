from bot_instance import bot

from handlers import start

from database.db import init_db


# ----- Flask Server -----
from flask import Flask
import threading
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "📚 CETSU Syllabus Bot is alive!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# Start web server in seperate thread
threading.Thread(target=run_web).start()




# ---- Start Everything ---- 

init_db()

bot.infinity_polling(timeout=10, long_polling_timeout=5)