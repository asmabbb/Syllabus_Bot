import urllib.parse
import re

from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from bot.bot_instance import bot as global_bot
from bot.database.queries.majors import get_majors
from bot.database.queries.semesters import get_semester_id, get_semesters_by_major
from bot.database.queries.subjects import get_subjects
from bot.database.queries.resources import get_resources, get_all_resources, get_categories_for_subject
from bot.config import ADMINS
from bot.utils.pagination import paginate, pagination_keyboard, ITEMS_PER_PAGE

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


def normalize(text):
    return re.sub(r'\s+', ' ', text.strip().lower())

# =========================
# CALLBACK HANDLERS (GLOBAL)
# =========================

def open_title(call):
    call.answer()

    print(f"[CALLBACK] {call.data}")

    try:
        _, title_index = call.data.split(":", 1)
        title_index = int(title_index)
    except Exception as e:
        print(f"[ERROR] open_title failed: {call.data} | {e}")
        return

    chat_id = call.message.chat.id
    data = resource_state.get(chat_id)
    if not data:
        global_bot.answer_callback_query(call.id, "No resources loaded. Please choose a category first.")
        return

    titles = data.get("titles", [])
    if title_index < 0 or title_index >= len(titles):
        print(f"[ERROR] open_title invalid title_index: {title_index}")
        return

    title = titles[title_index]
    data["current_title_index"] = title_index

    print(f"[DEBUG] Opening title: {title} (index {title_index})")

    send_files_page(chat_id, title, title_index, 0, call)


def send_file(call):
    call.answer()

    print(f"[CALLBACK] file -> {call.data}")

    try:
        _, title_index, file_index = call.data.split(":", 2)
        title_index = int(title_index)
        file_index = int(file_index)
    except Exception as e:
        print(f"[ERROR] send_file failed: {call.data} | {e}")
        return

    chat_id = call.message.chat.id
    data = resource_state.get(chat_id)
    if not data:
        return

    titles = data.get("titles", [])
    if title_index < 0 or title_index >= len(titles):
        return

    title = titles[title_index]
    items = data.get("grouped", {}).get(title)
    if not items or file_index < 0 or file_index >= len(items):
        return

    file_id = items[file_index][0]
    global_bot.send_document(chat_id, file_id)


def titles_pagination(call):
    call.answer()

    print(f"[CALLBACK] pagination -> {call.data}")

    try:
        _, _, page = call.data.split(":")
        page = int(page)
    except Exception as e:
        print(f"[ERROR] titles_pagination failed: {call.data} | {e}")
        return

    send_titles_page(call.message.chat.id, page, call.message.message_id)


def files_pagination(call):
    call.answer()

    print(f"[CALLBACK] files pagination -> {call.data}")

    try:
        _, title_index, _, page = call.data.split(":")
        title_index = int(title_index)
        page = int(page)
    except Exception as e:
        print(f"[ERROR] files_pagination failed: {call.data} | {e}")
        return

    chat_id = call.message.chat.id
    data = resource_state.get(chat_id)
    if not data:
        return

    titles = data.get("titles", [])
    if title_index < 0 or title_index >= len(titles):
        return

    title = titles[title_index]
    send_files_page(chat_id, title, title_index, page, call)


def back_to_titles(call):
    call.answer()

    send_titles_page(call.message.chat.id, 0, call.message.message_id)


# =========================
# MAIN REGISTER FUNCTION
# =========================

def register_syllabus(bot):

    # ===== Register Callbacks FIRST =====
    bot.callback_query_handler(func=lambda c: c.data.startswith("title:"))(open_title)
    bot.callback_query_handler(func=lambda c: c.data.startswith("file:"))(send_file)
    bot.callback_query_handler(func=lambda c: c.data.startswith("titles:page:"))(titles_pagination)
    bot.callback_query_handler(func=lambda c: c.data.startswith("files:"))(files_pagination)
    bot.callback_query_handler(func=lambda c: c.data == "back_titles")(back_to_titles)

    # ===== Syllabus Entry =====
    @bot.message_handler(func=lambda m: m.text == "📚 Syllabus")
    def syllabus(message):

        majors = get_majors()

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        for m in majors:
            markup.add(m[1])
        markup.add("⬅ Back")

        push(message.chat.id, markup)

        bot.send_message(message.chat.id, "Choose Major:", reply_markup=markup)

    # ===== Debug =====
    @bot.message_handler(func=lambda m: m.text == "/debug_resources")
    def debug_resources(message):
        if message.from_user.id not in ADMINS:
            return

        try:
            all_resources = get_all_resources()
            bot.send_message(message.chat.id, f"{all_resources[:5]}")
        except Exception as e:
            bot.send_message(message.chat.id, f"DB Error: {e}")

    # ===== Navigation =====
    @bot.message_handler(func=lambda m: True, content_types=['text'])
    def navigation(message):

        chat_id = message.chat.id
        text = message.text

        print(f"[NAVIGATION] {text}")

        if text == "📚 Syllabus":
            return

        if text == "⬅ Back":
            prev = back(chat_id)
            if prev:
                bot.send_message(chat_id, "Back", reply_markup=prev)
            return

        # MAJOR
        for m in get_majors():
            if text.strip() == m[1].strip():

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
                clean = normalize(title)

                if clean not in grouped:
                    grouped[clean] = []
                    title_map[clean] = title

                grouped[clean].append((file_id, year, season))

            sorted_titles = sorted(
                grouped.keys(),
                key=lambda t: max((y, s) for _, y, s in grouped[t]),
                reverse=True
            )

            resource_state[chat_id] = {
                "grouped": grouped,
                "titles": sorted_titles,
                "title_map": title_map
            }

            send_titles_page(chat_id, 0)
            return


# =========================
# UI FUNCTIONS
# =========================

def send_titles_page(chat_id, page, message_id=None):

    data = resource_state.get(chat_id)
    if not data:
        return

    titles = data.get("titles", [])
    page_items = paginate(titles, page)

    markup = InlineKeyboardMarkup()

    for index, title in enumerate(page_items):
        global_index = page * ITEMS_PER_PAGE + index
        display = data["title_map"].get(title, title)

        markup.add(
            InlineKeyboardButton(
                f"📘 {display}",
                callback_data=f"title:{global_index}"
            )
        )

    nav = pagination_keyboard("titles", page, len(titles))
    if nav.keyboard:
        for row in nav.keyboard:
            markup.row(*row)

    if message_id:
        global_bot.edit_message_text(
            "📚 Choose Resource Title:",
            chat_id,
            message_id,
            reply_markup=markup
        )
    else:
        global_bot.send_message(
            chat_id,
            "📚 Choose Resource Title:",
            reply_markup=markup
        )


def send_files_page(chat_id, title, title_index, page, call):

    data = resource_state.get(chat_id)
    if not data:
        return

    items = data.get("grouped", {}).get(title)
    if not items:
        global_bot.send_message(chat_id, "No files found.")
        return

    def season_order(s):
        return {"fall": 3, "summer": 2, "spring": 1}.get(s, 0)

    sorted_items = sorted(items, key=lambda x: (x[1], season_order(x[2])), reverse=True)
    data["current_title_index"] = title_index
    data["current_files"] = sorted_items

    page_items = paginate(sorted_items, page)

    markup = InlineKeyboardMarkup()

    for idx, (file_id, year, season) in enumerate(page_items):
        global_index = page * ITEMS_PER_PAGE + idx
        markup.add(
            InlineKeyboardButton(
                f"{season.capitalize()} {year}",
                callback_data=f"file:{title_index}:{global_index}"
            )
        )

    nav = pagination_keyboard(f"files:{title_index}", page, len(sorted_items))
    if nav.keyboard:
        for row in nav.keyboard:
            markup.row(*row)

    markup.add(InlineKeyboardButton("⬅ Back", callback_data="back_titles"))

    global_bot.edit_message_text(
        f"📘 {data['title_map'].get(title, title)}",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )