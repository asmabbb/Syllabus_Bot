from collections import defaultdict
import urllib.parse

from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from bot.database.queries.majors import get_majors
from bot.database.queries.semesters import get_semester_id
from bot.database.queries.subjects import get_subjects
from bot.database.queries.resources import get_resources
from bot.database.queries.semesters import get_semesters_by_major
from bot.utils.pagination import paginate, pagination_keyboard

user_state = {}
user_history = {}
resource_state = {}


def push(chat_id, markup):
    user_history.setdefault(chat_id, []).append(markup)


def back(chat_id):
    if chat_id not in user_history or len(user_history[chat_id]) <= 1:
        return None
    user_history[chat_id].pop()
    return user_history[chat_id][-1]


def register_syllabus(bot):

    def syllabus(message):

        majors = get_majors()

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        for m in majors:
            markup.add(m[1])
        markup.add("⬅ Back")

        push(message.chat.id, markup)

        bot.send_message(message.chat.id, "Choose Major:", reply_markup=markup)

    bot.message_handler(func=lambda m: m.text == "📚 Syllabus")(syllabus)

    def navigation(message):

        chat_id = message.chat.id
        text = message.text

        print(f"[NAVIGATION] Received: {text}")

        if text == "📚 Syllabus":
            return

        # BACK
        if text == "⬅ Back":
            prev = back(chat_id)
            if prev:
                bot.send_message(chat_id, "Back", reply_markup=prev)
            return

        # MAJOR
        majors = get_majors()

        print(f"[DEBUG] majors from DB: {majors}")

        for m in majors:
            if text.strip() == m[1].strip():

                print(f"[MATCH] Selected major: {m[1]}")

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
            mapping = {
                "Exam": "exam",
                "Books & Lectures": "books & lectures",
                "Other Resources": "other resources"
            }

            category = mapping.get(text)

            if not category:
                print(f"[ERROR] Unknown category: {text}")
                return

            resources = get_resources(
                user_state[chat_id]["subject_id"],
                category
            )

            if not resources:
                bot.send_message(chat_id, "No resources found.")
                return

            grouped = {}
            title_map = {}

            for title, file_id, year, season in resources:
                clean = title.strip().lower()

                if clean not in grouped:
                    grouped[clean] = []
                    title_map[clean] = title  # keep original

                grouped[clean].append((file_id, year, season))

            sorted_titles = sorted(
                grouped.keys(),
                key=lambda t: max((y, s) for _, y, s in grouped[t]),
                reverse=True
            )

            # Save everything in state
            resource_state[chat_id] = {
                "grouped": grouped,
                "titles": sorted_titles,
                "title_map": title_map,
                "category": category
            }

            send_titles_page(bot, chat_id, 0)
            return

        print(f"[WARNING] Unhandled input: {text}")

    bot.message_handler(func=lambda m: True, content_types=['text'])(navigation)


    def send_titles_page(bot, chat_id, page):

        data = resource_state.get(chat_id)
        if not data:
            return

        titles = data["titles"]

        page_items = paginate(titles, page)

        markup = InlineKeyboardMarkup()

        for title in page_items:
            display = data["title_map"][title]
            markup.add(
                InlineKeyboardButton(
                    f"📘 {display}",
                    callback_data=f"title:{title}:0"
                )
            )

        nav = pagination_keyboard("titles", page, len(titles))
        if nav.keyboard:
            for row in nav.keyboard:
                markup.row(*row)

        bot.send_message(chat_id, "📚 Choose Resource Title:", reply_markup=markup)


    def send_files_page(bot, chat_id, title, page, message_id):

        data = resource_state.get(chat_id)
        if not data:
            return

        title_key = title.strip().lower()

        print(f"[DEBUG] Requested: '{title_key}'")
        print(f"[DEBUG] Available: {list(data['grouped'].keys())}")

        items = data["grouped"].get(title_key)

        if not items:
            bot.send_message(chat_id, "No files found for this title.")
            return

        def season_order(season):
            return {"fall": 3, "summer": 2, "spring": 1}.get(season, 0)

        items = sorted(
            items,
            key=lambda x: (x[1], season_order(x[2])),
            reverse=True
        )

        page_items = paginate(items, page)

        markup = InlineKeyboardMarkup()

        for file_id, year, season in page_items:
            markup.add(
                InlineKeyboardButton(
                    f"{season.capitalize()} {year}",
                    callback_data=f"file:{file_id}"
                )
            )

        # pagination
        nav = pagination_keyboard(f"title:{title}", page, len(items))
        if nav.keyboard:
            for row in nav.keyboard:
                markup.row(*row)

        # back button
        markup.add(
            InlineKeyboardButton("⬅ Back", callback_data="back_titles")
        )

        display = data["title_map"].get(title, title)

        bot.edit_message_text(
            f"📘 {display}",
            chat_id,
            message_id,
            reply_markup=markup
        )


    def back_to_titles(call):

        chat_id = call.message.chat.id

        send_titles_page(bot, chat_id, 0)

    bot.callback_query_handler(func=lambda c: c.data == "back_titles")(back_to_titles)


    def open_title(call):
        try:
            _, title, page = call.data.split(":", 2)
            page = int(page)
        except Exception as e:
            print(f"[ERROR] open_title failed: {call.data} | {e}")
            return

        title = title.strip().lower()
        chat_id = call.message.chat.id

        print(f"[DEBUG] Opening title: '{title}'")

        send_files_page(bot, chat_id, title, page, call.message.message_id)

    bot.callback_query_handler(func=lambda c: c.data.startswith("title:"))(open_title)


    def send_file(call):
        try:
            _, file_id = call.data.split(":", 1)
        except ValueError:
            return

        bot.send_document(
            call.message.chat.id,
            file_id
        )

    bot.callback_query_handler(func=lambda c: c.data.startswith("file:"))(send_file)