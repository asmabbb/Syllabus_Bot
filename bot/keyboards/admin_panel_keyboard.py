from telebot.types import ReplyKeyboardMarkup


def admin_menu():

    markup = ReplyKeyboardMarkup(resize_keyboard=True)

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