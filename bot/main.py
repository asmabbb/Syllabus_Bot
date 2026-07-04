from bot.bot_instance import bot

from bot.handlers import start as start_handler
from bot.handlers.admin_panel import register_admin_panel
from bot.handlers.syllabus import register_syllabus
from bot.handlers.share import register_share_handlers

from bot.database.db import init_db

# -------------------------
# REGISTER HANDLERS
# -------------------------
register_share_handlers(bot)
register_admin_panel(bot)
register_syllabus(bot)

# -------------------------
# STARTUP
# -------------------------
if __name__ == "__main__":
    init_db()

    print("Starting bot in polling mode...")

    bot.remove_webhook()

    print("Bot is running...")

    bot.infinity_polling()