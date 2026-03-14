from telebot.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu(is_admin = False):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        KeyboardButton("📚 Syllabus"),
        KeyboardButton("📤 Share Resources"),
        KeyboardButton("📁 Archive")
    )

    if is_admin:
        markup.add("⚙️ Admin Panel")

    return markup