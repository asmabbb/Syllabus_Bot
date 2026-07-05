from telebot.types import ReplyKeyboardMarkup
from bot.utils.permissions import is_super_admin, is_owner


def admin_menu(user_id):

    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    if is_super_admin(user_id):

        markup.add("Manage Admins")
        markup.add("Manage Majors")
        markup.add("Manage Subjects")

    markup.add("Manage Resources")

    markup.add("⬅ Back")

    return markup


def majors_menu():

    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("Add Major")
    markup.add("Edit Major")
    markup.add("Delete Major")

    markup.add("⬅ Back")

    return markup


def subjects_menu():

    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("Add Subject")
    markup.add("Delete Subject")

    markup.add("⬅ Back")

    return markup


def manage_admins_menu():

    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("View Admins")
    markup.add("Add Admin")
    markup.add("Remove Admin")
    markup.add("⬅ Back")

    return markup


def add_admin_menu(user_id):

    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("Minor Admin")

    if is_owner(user_id):
        markup.add("Superior Admin")
    markup.add("⬅ Back")

    return markup


def remove_admin_menu(user_id):

    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("Minor Admin")

    if is_owner(user_id):
        markup.add("Superior Admin")

    markup.add("⬅ Back")

    return markup

