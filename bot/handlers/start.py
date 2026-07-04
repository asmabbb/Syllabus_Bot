from bot.bot_instance import bot
from bot.database.queries.users import get_user, create_user
from bot.keyboards.main_menu_keyboard import main_menu
from bot.config import is_admin, is_super_admin
from bot.handlers.admin_panel import admin_state


@bot.message_handler(commands=['start'])
def start_handler(message):
    admin_state.pop(message.chat.id, None)

    user_id = message.from_user.id
    admin = is_admin(user_id)
    chat_id = message.chat.id

    user = get_user(user_id)

    if not user:
        create_user(user_id, "student")

    bot.send_message(chat_id, f"Welcome {message.from_user.first_name} to the Syllabus Bot!", reply_markup=main_menu(admin))