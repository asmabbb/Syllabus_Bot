from bot_instance import bot

from handlers import start

from database.db import init_db


init_db()

bot.infinity_polling()