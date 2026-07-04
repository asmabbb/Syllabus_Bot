import telebot
from bot.config import BOT_TOKEN

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML",
    threaded=True
    )