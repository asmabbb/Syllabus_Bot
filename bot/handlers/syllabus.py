import re
from telebot.types import ReplyKeyboardMarkup
from bot.bot_instance import bot as global_bot
from bot.database.queries.majors import get_majors
from bot.database.queries.semesters import get_semester_id, get_semesters_by_major
from bot.database.queries.subjects import get_subjects
from bot.database.queries.resources import get_resources
from bot.config import ADMINS
from bot.utils.pagination import paginate, ITEMS_PER_PAGE

user_state = {}
resource_state = {}

# =========================
# HELPERS
# =========================

def normalize(text):
    return re.sub(r'\s+', ' ', text.strip().lower())


def categories_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Exam", "Books & Lectures", "Other Resources")
    markup.add("⬅ Back")
    return markup


def main_menu(chat_id, user_id):
    from bot.keyboards.main_menu_keyboard import main_menu
    bot.send_message(chat_id, "Main Menu", reply_markup=main_menu(user_id in ADMINS))


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

        user_state[chat_id] = {"stack": []}
        resource_state.pop(chat_id, None)

        majors = get_majors()

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        for m in majors:
            markup.add(m[1])
        markup.add("⬅ Back")

        bot.send_message(chat_id, "Choose Major:", reply_markup=markup)


    # =========================
    # BACK BUTTON (⬅)
    # =========================
    @bot.message_handler(func=lambda m: m.text == "⬅ Back")
    def back_button(message):
        chat_id = message.chat.id

        # If viewing titles → go back to categories
        if resource_state.get(chat_id, {}).get("viewing_titles"):
            resource_state[chat_id]["viewing_titles"] = False
            bot.send_message(chat_id, "Choose Type:", reply_markup=categories_keyboard())
            return

        go_back(chat_id, message.from_user.id)


    # =========================
    # /BACK COMMAND
    # =========================
    @bot.message_handler(commands=['back'])
    def back_command(message):
        chat_id = message.chat.id

        # ALWAYS go to categories if possible
        state = user_state.get(chat_id, {})
        stack = state.get("stack", [])

        # If inside subject → show categories
        if stack and any(s["level"] == "subject" for s in stack):
            resource_state.pop(chat_id, None)
            bot.send_message(chat_id, "Choose Type:", reply_markup=categories_keyboard())
            return

        # Otherwise fallback
        go_back(chat_id, message.from_user.id)


    # =========================
    # CORE BACK LOGIC
    # =========================
    def go_back(chat_id, user_id):

        state = user_state.get(chat_id)
        if not state or not state.get("stack"):
            main_menu(chat_id, user_id)
            return

        stack = state["stack"]

        # remove ONE level
        stack.pop()

        if not stack:
            main_menu(chat_id, user_id)
            return

        last = stack[-1]

        # ===== REBUILD UI =====

        if last["level"] == "major":
            semesters = get_semesters_by_major(last["major_id"])

            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            for s in semesters:
                markup.add(f"Semester {s}")
            markup.add("⬅ Back")

            bot.send_message(chat_id, "Choose Semester:", reply_markup=markup)

        elif last["level"] == "semester":
            semester_id = get_semester_id(stack[0]["major_id"], last["semester"])
            subjects = get_subjects(semester_id)

            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            for s in subjects:
                markup.add(s[1])
            markup.add("⬅ Back")

            bot.send_message(chat_id, "Choose Subject:", reply_markup=markup)

        elif last["level"] == "subject":
            bot.send_message(chat_id, "Choose Type:", reply_markup=categories_keyboard())


    # =========================
    # TITLE SELECTION
    # =========================
    @bot.message_handler(func=lambda m: m.text and m.text.isdigit() and resource_state.get(m.chat.id, {}).get("viewing_titles"))
    def handle_title(message):
        chat_id = message.chat.id
        data = resource_state.get(chat_id)

        try:
            idx = int(message.text) - 1
            titles = data["titles"]

            if idx < 0 or idx >= len(titles):
                bot.send_message(chat_id, "Invalid number.")
                return

            title = titles[idx]
            items = data["grouped"][title]

            bot.send_message(chat_id, f"📘 {data['title_map'][title]}")

            for file_id, year, season in items:
                bot.send_document(
                    chat_id,
                    file_id,
                    caption=f"{(season or 'Unknown').capitalize()} {year or 'Unknown'}"
                )

        except:
            bot.send_message(chat_id, "Invalid input.")


    # =========================
    # PAGINATION
    # =========================
    @bot.message_handler(func=lambda m: m.text == "/next" and resource_state.get(m.chat.id, {}).get("viewing_titles"))
    def next_page(message):
        data = resource_state[message.chat.id]
        page = data.get("current_page", 0)
        send_titles_page(message.chat.id, page + 1)


    @bot.message_handler(func=lambda m: m.text == "/prev" and resource_state.get(m.chat.id, {}).get("viewing_titles"))
    def prev_page(message):
        data = resource_state[message.chat.id]
        page = data.get("current_page", 0)
        if page > 0:
            send_titles_page(message.chat.id, page - 1)


    # =========================
    # NAVIGATION
    # =========================
    @bot.message_handler(func=lambda m: True, content_types=['text'])
    def navigation(message):

        chat_id = message.chat.id
        text = message.text.strip()

        # block navigation during titles
        if resource_state.get(chat_id, {}).get("viewing_titles"):
            return

        state = user_state.setdefault(chat_id, {"stack": []})
        stack = state["stack"]

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

            stack.append({"level": "semester", "semester": sem})

            semester_id = get_semester_id(stack[0]["major_id"], sem)
            subjects = get_subjects(semester_id)

            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            for s in subjects:
                markup.add(s[1])
            markup.add("⬅ Back")

            bot.send_message(chat_id, "Choose Subject:", reply_markup=markup)
            return

        # ===== SUBJECT =====
        if stack and stack[-1]["level"] == "semester":

            semester_id = get_semester_id(stack[0]["major_id"], stack[-1]["semester"])
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

            resources = get_resources(subject_id, category)
            if not resources:
                bot.send_message(chat_id, "No resources found.")
                return

            grouped, title_map = {}, {}

            for title, file_id, year, season in resources:
                clean = normalize(title)
                grouped.setdefault(clean, []).append((file_id, year, season))
                title_map[clean] = title

            titles = sorted(
                grouped.keys(),
                key=lambda t: max((y or 0, s or '') for _, y, s in grouped[t]),
                reverse=True
            )

            resource_state[chat_id] = {
                "grouped": grouped,
                "titles": titles,
                "title_map": title_map,
                "viewing_titles": True,
                "current_page": 0
            }

            send_titles_page(chat_id, 0)


# =========================
# UI
# =========================

def send_titles_page(chat_id, page):

    data = resource_state.get(chat_id)
    if not data:
        return

    titles = data["titles"]
    total_pages = (len(titles) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    page = max(0, min(page, total_pages - 1))
    data["current_page"] = page

    page_items = paginate(titles, page)

    lines = []
    for i, t in enumerate(page_items):
        idx = page * ITEMS_PER_PAGE + i + 1
        lines.append(f"{idx}. {data['title_map'][t]}")

    text = f"📚 Page {page+1}/{total_pages}\n\n" + "\n".join(lines)
    text += "\n\nSend number\n/prev | /next | /back"

    global_bot.send_message(chat_id, text)