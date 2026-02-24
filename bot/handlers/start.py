from bot.bot_instance import bot
from bot.database.queries.users import get_user, create_user
from bot.keyboards.main_menu_keyboard import main_menu
from bot.config import ADMINS


@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    is_admin = user_id in ADMINS
    chat_id = message.chat.id

    user = get_user(user_id)

    if not user:
        role = "admin" if user_id in ADMINS else "student"
        create_user(user_id, role)

    bot.send_message(chat_id, f"Welcome {message.from_user.first_name} to the Syllabys Bot!", reply_markup=main_menu(is_admin))