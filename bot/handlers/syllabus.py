from collections import defaultdict

from telebot.types import ReplyKeyboardMarkup
from bot.database.queries.majors import get_majors
from bot.database.queries.semesters import get_semester_id
from bot.database.queries.subjects import get_subjects
from bot.database.queries.resources import get_resources
from bot.database.queries.semesters import get_semesters_by_major

user_state = {}
user_history = {}


def push(chat_id, markup):
    user_history.setdefault(chat_id, []).append(markup)


def back(chat_id):
    if chat_id not in user_history or len(user_history[chat_id]) <= 1:
        return None
    user_history[chat_id].pop()
    return user_history[chat_id][-1]


def register_syllabus(bot):

    @bot.message_handler(func=lambda m: m.text == "📚 Syllabus")
    def syllabus(message):

        majors = get_majors()

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        for m in majors:
            markup.add(m[1])
        markup.add("⬅ Back")

        push(message.chat.id, markup)

        bot.send_message(message.chat.id, "Choose Major:", reply_markup=markup)


    @bot.message_handler(func=lambda m: True)
    def navigation(message):

        chat_id = message.chat.id
        text = message.text

        # BACK
        if text == "⬅ Back":
            prev = back(chat_id)
            if prev:
                bot.send_message(chat_id, "Back", reply_markup=prev)
            return

        # MAJOR
        for m in get_majors():
            if text == m[1]:

                user_state[chat_id] = {"major_id": m[0]}

                semesters = get_semesters_by_major(m[0])

                markup = ReplyKeyboardMarkup(resize_keyboard=True)
                for s in semesters:
                    markup.add(f"Semester {s}")

                markup.add("⬅ Back")

                push(chat_id, markup)

                bot.send_message(chat_id, "Choose Semester:", reply_markup=markup)
                return

        # SEMESTER
        if chat_id in user_state and "major_id" in user_state[chat_id]:
            if text.startswith("Semester"):

                sem_number = int(text.split()[1])
                user_state[chat_id]["semester"] = sem_number

                semester_id = get_semester_id(user_state[chat_id]["major_id"], sem_number)
                subjects = get_subjects(semester_id)

                markup = ReplyKeyboardMarkup(resize_keyboard=True)
                for s in subjects:
                    markup.add(s[1])

                markup.add("⬅ Back")

                push(chat_id, markup)

                bot.send_message(chat_id, "Choose Subject:", reply_markup=markup)
                return

        # SUBJECT
        if "semester" in user_state.get(chat_id, {}):
            semester_id = get_semester_id(
                user_state[chat_id]["major_id"],
                user_state[chat_id]["semester"]
            )
            subjects = get_subjects(semester_id)

            for s in subjects:
                if text == s[1]:

                    user_state[chat_id]["subject_id"] = s[0]

                    markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    markup.add("Exam", "Books & Lectures", "Other Resources")
                    markup.add("⬅ Back")

                    push(chat_id, markup)

                    bot.send_message(chat_id, "Choose Type:", reply_markup=markup)
                    return

        # CATEGORY
        if "subject_id" in user_state.get(chat_id, {}):
            category = text.lower()

            resources = get_resources(
                user_state[chat_id]["subject_id"],
                category
            )

            if not resources:
                bot.send_message(chat_id, "No resources found.")
                return

            grouped = defaultdict(list)

            for title, file_id, year, season in resources:
                grouped[title].append((file_id, year, season))

            # Sort titles newest first (based on latest resource inside)
            sorted_titles = sorted(
                grouped.keys(),
                key=lambda t: max((y, s) for _, y, s in grouped[t]),
                reverse=True
            )

            for title in sorted_titles:

                bot.send_message(chat_id, f"📚 {title}")

                # Sort inside each title
                items = sorted(
                    grouped[title],
                    key=lambda x: (x[1], x[2]),
                    reverse=True
                )

                for file_id, year, season in items:
                    bot.send_document(
                        chat_id,
                        file_id,
                        caption=f"{season.capitalize()} {year}"
                    )