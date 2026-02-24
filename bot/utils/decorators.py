from config import ADMINS

def admin_only(func):
    def wrapper(message, bot):
        if message.from_user.id not in ADMINS:
            bot.send_message(message.chat.id, "Access denied.")
            return
        return func(message, bot)
    return wrapper