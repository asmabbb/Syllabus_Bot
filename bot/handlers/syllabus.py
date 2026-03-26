import re
from telebot.types import ReplyKeyboardMarkup

from bot.database.queries.majors import get_majors
from bot.database.queries.semesters import get_semester_id, get_semesters_by_major
from bot.database.queries.subjects import get_subjects
from bot.database.queries.resources import get_resources
from bot.config import ADMINS
from bot.utils.pagination import paginate, ITEMS_PER_PAGE
from bot.bot_instance import bot as global_bot

user_state = {}
resource_state = {}


def normalize(text):
    return re.sub(r'\s+', ' ', text.strip().lower())


# =========================
# KEYBOARD BUILDERS
# =========================

def categories_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Exam", "Books & Lectures", "Other Resources")
    markup.add("⬅ Back")
    return markup


def back_only_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("⬅ Back")
    return markup


# =========================
# MAIN REGISTER FUNCTION
# =========================

def register_syllabus(bot):

    # =========================
    # ENTRY
    # =========================
    @bot.message_handler(func=lambda m: m.text == "📚 Syllabus")
    def syllabus(message):
        chat_id = message.chat.id

        majors = get_majors()

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        for m in majors:
            markup.add(m[1])
        markup.add("⬅ Back")

        user_state[chat_id] = {"stack": []}

        bot.send_message(chat_id, "Choose Major:", reply_markup=markup)


    # =========================
    # BACK BUTTON
    # =========================
    @bot.message_handler(func=lambda m: m.text == "⬅ Back")
    def handle_back_button(message):
        chat_id = message.chat.id

        # If viewing titles → go back to categories ONLY
        if resource_state.get(chat_id, {}).get("viewing_titles"):
            resource_state[chat_id]["viewing_titles"] = False

            bot.send_message(chat_id, "Choose Type:", reply_markup=categories_keyboard())
            return

        _go_back(chat_id, message.from_user.id)


    # =========================
    # /BACK COMMAND
    # =========================
    @bot.message_handler(commands=['back'])
    def handle_back_command(message):
        chat_id = message.chat.id

        # ALWAYS go to categories if inside subject
        stack = user_state.get(chat_id, {}).get("stack", [])

        for item in reversed(stack):
            if item["level"] == "subject":
                resource_state[chat_id] = {"viewing_titles": False}
                bot.send_message(chat_id, "Choose Type:", reply_markup=categories_keyboard())
                return

        # fallback
        _go_back(chat_id, message.from_user.id)


    # =========================
    # NAVIGATION
    # =========================
    @bot.message_handler(func=lambda m: True, content_types=['text'])
    def navigation(message):

        chat_id = message.chat.id
        text = message.text.strip()

        if resource_state.get(chat_id, {}).get("viewing_titles"):
            return

        if text == "📚 Syllabus":
            return

        state = user_state.setdefault(chat_id, {})
        stack = state.setdefault("stack", [])

        # ===== MAJOR =====
        for m in get_majors():
            if text == m[1]:
                stack.clear()
                stack.append({"level": "major", "major_id": m[0]})

                semesters = get_semesters_by_major(m[0])

                markup = ReplyKeyboardMarkup(resize_keyboard=True)
                for s in semesters:
                    markup.add(f"Semester {s}")
                markup.add("⬅ Back")

                bot.send_message(chat_id, "Choose Semester:", reply_markup=markup)
                return

        # ===== SEMESTER =====
        if stack and stack[-1]["level"] == "major" and text.startswith("Semester"):
            sem = int(text.split()[1])
            major_id = stack[-1]["major_id"]

            stack.append({"level": "semester", "semester": sem})

            semester_id = get_semester_id(major_id, sem)
            subjects = get_subjects(semester_id)

            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            for s in subjects:
                markup.add(s[1])
            markup.add("⬅ Back")

            bot.send_message(chat_id, "Choose Subject:", reply_markup=markup)
            return

        # ===== SUBJECT =====
        if stack and stack[-1]["level"] == "semester":
            major_id = stack[0]["major_id"]
            sem = stack[-1]["semester"]

            semester_id = get_semester_id(major_id, sem)
            subjects = get_subjects(semester_id)

            for s in subjects:
                if text == s[1]:
                    stack.append({"level": "subject", "subject_id": s[0]})

                    bot.send_message(chat_id, "Choose Type:", reply_markup=categories_keyboard())
                    return

        # ===== CATEGORY =====
        if stack and stack[-1]["level"] == "subject":

            mapping = {
                "Exam": "exam",
                "Books & Lectures": "books & lectures",
                "Other Resources": "other resources"
            }

            category = mapping.get(text)
            if not category:
                return

            subject_id = stack[-1]["subject_id"]

            stack.append({"level": "category", "category": category})

            resources = get_resources(subject_id, category)

            if not resources:
                bot.send_message(chat_id, "No resources found.")
                return

            grouped = {}
            title_map = {}

            for title, file_id, year, season in resources:
                if not title or not file_id:
                    continue

                clean = normalize(title)

                grouped.setdefault(clean, []).append((file_id, year or 0, season or ''))
                title_map[clean] = title

            sorted_titles = sorted(
                grouped.keys(),
                key=lambda t: max((y, s) for _, y, s in grouped[t]),
                reverse=True
            )

            resource_state[chat_id] = {
                "grouped": grouped,
                "titles": sorted_titles,
                "title_map": title_map,
                "viewing_titles": True
            }

            send_titles_page(chat_id, 0)
            return


    # =========================
    # TITLE SELECTION
    # =========================
    @bot.message_handler(func=lambda m: m.text.isdigit() and resource_state.get(m.chat.id, {}).get("viewing_titles"))
    def handle_title(message):

        chat_id = message.chat.id
        data = resource_state.get(chat_id)

        index = int(message.text) - 1
        titles = data["titles"]

        if index < 0 or index >= len(titles):
            bot.send_message(chat_id, "Invalid number.")
            return

        title = titles[index]
        items = data["grouped"][title]

        bot.send_message(chat_id, f"📘 {data['title_map'][title]}")

        for file_id, year, season in items:
            bot.send_document(chat_id, file_id, caption=f"{season} {year}")


# =========================
# BACK LOGIC
# =========================

def _go_back(chat_id, user_id):

    stack = user_state.get(chat_id, {}).get("stack", [])

    if not stack:
        from bot.keyboards.main_menu_keyboard import main_menu
        global_bot.send_message(chat_id, "Main Menu", reply_markup=main_menu(user_id in ADMINS))
        return

    stack.pop()

    if not stack:
        from bot.keyboards.main_menu_keyboard import main_menu
        global_bot.send_message(chat_id, "Main Menu", reply_markup=main_menu(user_id in ADMINS))
        return

    last = stack[-1]

    if last["level"] == "major":
        semesters = get_semesters_by_major(last["major_id"])

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        for s in semesters:
            markup.add(f"Semester {s}")
        markup.add("⬅ Back")

        global_bot.send_message(chat_id, "Choose Semester:", reply_markup=markup)

    elif last["level"] == "semester":
        semester_id = get_semester_id(stack[0]["major_id"], last["semester"])
        subjects = get_subjects(semester_id)

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        for s in subjects:
            markup.add(s[1])
        markup.add("⬅ Back")

        global_bot.send_message(chat_id, "Choose Subject:", reply_markup=markup)

    elif last["level"] == "subject":
        global_bot.send_message(chat_id, "Choose Type:", reply_markup=categories_keyboard())


# =========================
# PAGINATION
# =========================

def send_titles_page(chat_id, page):

    data = resource_state.get(chat_id)
    titles = data["titles"]

    page_items = paginate(titles, page)

    text = "\n".join(
        f"{i + 1 + page * ITEMS_PER_PAGE}. {data['title_map'][t]}"
        for i, t in enumerate(page_items)
    )

    global_bot.send_message(
        chat_id,
        f"📚 Page {page+1}\n\n{text}\n\nSend number.\n/back → categories"
    )

    data["current_page"] = page