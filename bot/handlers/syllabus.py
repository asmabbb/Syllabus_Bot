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

        # BACK
        if text == "⬅ Back":
            prev = back(chat_id)
            if prev:
                bot.send_message(chat_id, "Back", reply_markup=prev)
            return

        # MAJOR
        majors = get_majors()

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

            sorted_titles = sorted(
                grouped.keys(),
                key=lambda t: max((y, s) for _, y, s in grouped[t]),
                reverse=True
            )

            # Save everything in state
            resource_state[chat_id] = {
                "grouped": grouped,
                "titles": sorted_titles,
                "category": category
            }

            send_titles_page(bot, chat_id, 0)
            return

        print(f"[WARNING] Unhandled input: {text}")

    bot.message_handler(func=lambda m: m.text is not None)(navigation)


    def send_titles_page(bot, chat_id, page):

        data = resource_state.get(chat_id)
        if not data:
            return

        titles = data["titles"]

        page_items = paginate(titles, page)

        markup = InlineKeyboardMarkup()

        for title in page_items:
            safe_title = urllib.parse.quote(title)
            markup.add(
                InlineKeyboardButton(
                    f"📘 {title}",
                    callback_data=f"title:{safe_title}:0"
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

        items = data["grouped"][title]

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
        safe_title = urllib.parse.quote(title)
        nav = pagination_keyboard(f"title:{safe_title}", page, len(items))
        if nav.keyboard:
            for row in nav.keyboard:
                markup.row(*row)

        # back button
        markup.add(
            InlineKeyboardButton("⬅ Back", callback_data="back_titles")
        )

        bot.edit_message_text(
            f"📘 {title}",
            chat_id,
            message_id,
            reply_markup=markup
        )


    def open_title(call):

        # Only handle title selection callbacks (not pagination callbacks)
        if ":page:" in call.data:
            return

        try:
            _, encoded_title, page = call.data.split(":", 2)
            page = int(page)
        except Exception:
            return

        title = urllib.parse.unquote(encoded_title)
        chat_id = call.message.chat.id

        send_files_page(bot, chat_id, title, page, call.message.message_id)

    bot.callback_query_handler(func=lambda c: c.data.startswith("title:") and ":page:" not in c.data)(open_title)


    def titles_page_handler(call):

        try:
            _, _, page = call.data.split(":", 2)
            page = int(page)
        except Exception:
            return

        chat_id = call.message.chat.id

        send_titles_page(bot, chat_id, page)

    bot.callback_query_handler(func=lambda c: c.data.startswith("titles:page"))(titles_page_handler)


    def back_to_titles(call):

        chat_id = call.message.chat.id

        send_titles_page(bot, chat_id, 0)

    bot.callback_query_handler(func=lambda c: c.data == "back_titles")(back_to_titles)


    def title_page_handler(call):
        # Handles pagination inside a specific title's file list
        try:
            # Format: title:<encoded_title>:page:<page>
            _, encoded_title, _, page = call.data.split(":", 3)
            page = int(page)
        except Exception:
            return

        title = urllib.parse.unquote(encoded_title)
        chat_id = call.message.chat.id

        send_files_page(bot, chat_id, title, page, call.message.message_id)

    bot.callback_query_handler(func=lambda c: c.data.startswith("title:") and ":page:" in c.data)(title_page_handler)


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