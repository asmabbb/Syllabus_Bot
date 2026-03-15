from telebot.types import ReplyKeyboardMarkup
from bot.database.queries.majors import get_majors
from bot.database.queries.subjects import get_subjects
from bot.database.queries.resources import get_resources

user_state = {}
user_history = {}


def push_history(chat_id, markup):
    if chat_id not in user_history:
        user_history[chat_id] = []

    user_history[chat_id].append(markup)


def go_back(chat_id):
    if chat_id not in user_history or len(user_history[chat_id]) <= 1:
        return None

    user_history[chat_id].pop()
    return user_history[chat_id][-1]


def register_syllabus(bot):

    @bot.message_handler(func=lambda m: m.text == "📚 Syllabus")
    def syllabus_menu(message):

        majors = get_majors()

        markup = ReplyKeyboardMarkup(resize_keyboard=True)

        for major in majors:
            markup.add(major[1])

        markup.add("⬅ Back")

        push_history(message.chat.id, markup)

        bot.send_message(
            message.chat.id,
            "Choose Major:",
            reply_markup=markup
        )


    @bot.message_handler(func=lambda m: True)
    def syllabus_navigation(message):

        chat_id = message.chat.id
        text = message.text

        # BACK BUTTON
        if text == "⬅ Back":

            previous = go_back(chat_id)

            if previous:
                bot.send_message(
                    chat_id,
                    "Going back...",
                    reply_markup=previous
                )
            return


        majors = get_majors()

        # MAJOR SELECTED
        for major in majors:
            if text == major[1]:

                user_state[chat_id] = {"major_id": major[0]}

                subjects = get_subjects(major[0])

                markup = ReplyKeyboardMarkup(resize_keyboard=True)

                for subject in subjects:
                    markup.add(subject[1])

                markup.add("⬅ Back")

                push_history(chat_id, markup)

                bot.send_message(
                    chat_id,
                    "Choose Subject:",
                    reply_markup=markup
                )

                return


        # SUBJECT SELECTED
        if chat_id in user_state and "major_id" in user_state[chat_id]:

            subjects = get_subjects(user_state[chat_id]["major_id"])

            for subject in subjects:
                if text == subject[1]:

                    user_state[chat_id]["subject_id"] = subject[0]

                    markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    markup.add("Exam")
                    markup.add("Books & Lectures")
                    markup.add("Other Resources")
                    markup.add("⬅ Back")

                    push_history(chat_id, markup)

                    bot.send_message(
                        chat_id,
                        "Choose Resource Type:",
                        reply_markup=markup
                    )

                    return


        # CATEGORY SELECTED
        if chat_id in user_state and "subject_id" in user_state[chat_id]:

            subject_id = user_state[chat_id]["subject_id"]

            category = text

            resources = get_resources(subject_id, category)

            if not resources:
                bot.send_message(chat_id, "No resources found.")
                return

            for title, file_id in resources:

                bot.send_document(
                    chat_id,
                    file_id,
                    caption=title
                )

            return