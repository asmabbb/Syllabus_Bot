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


def main_menu(chat_id, user_id):
    from bot.keyboards.main_menu_keyboard import main_menu
    global_bot.send_message(chat_id, "Main Menu", reply_markup=main_menu(user_id in ADMINS))


def categories_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Exam", "Books & Lectures", "Other Resources")
    markup.add("⬅ Back")
    return markup


# =========================
# MAIN HANDLER (SINGLE ROUTER)
# =========================

def register_syllabus(bot):

    @bot.message_handler(func=lambda m: True, content_types=['text'])
    def router(message):

        chat_id = message.chat.id
        text = message.text.strip()

        state = user_state.setdefault(chat_id, {"stack": []})
        stack = state["stack"]

        res_state = resource_state.get(chat_id)

        # =========================
        # ENTRY
        # =========================
        if text == "📚 Syllabus":
            user_state[chat_id] = {"stack": []}
            resource_state.pop(chat_id, None)

            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            for m in get_majors():
                markup.add(m[1])
            markup.add("⬅ Back")

            bot.send_message(chat_id, "Choose Major:", reply_markup=markup)
            return

        # =========================
        # BACK BUTTON (STEP BACK)
        # =========================
        if text == "⬅ Back":

            # If viewing titles → go to categories ONLY
            if res_state and res_state.get("viewing_titles"):
                res_state["viewing_titles"] = False
                bot.send_message(chat_id, "Choose Type:", reply_markup=categories_keyboard())
                return

            # Normal stack back
            if not stack:
                main_menu(chat_id, message.from_user.id)
                return

            stack.pop()

            if not stack:
                main_menu(chat_id, message.from_user.id)
                return

            last = stack[-1]

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

            return

        # =========================
        # /BACK → ALWAYS CATEGORIES
        # =========================
        if text == "/back":

            if stack:
                for i in reversed(range(len(stack))):
                    if stack[i]["level"] == "subject":
                        stack[:] = stack[:i+1]
                        break

            resource_state.pop(chat_id, None)
            bot.send_message(chat_id, "Choose Type:", reply_markup=categories_keyboard())
            return

        # =========================
        # PAGINATION
        # =========================
        if res_state and res_state.get("viewing_titles"):

            if text == "/next":
                send_titles_page(chat_id, res_state["current_page"] + 1)
                return

            if text == "/prev":
                send_titles_page(chat_id, res_state["current_page"] - 1)
                return

            if text.isdigit():
                handle_title_selection(chat_id, int(text))
                return

            return  # block navigation while browsing

        # =========================
        # MAJOR
        # =========================
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

        # =========================
        # SEMESTER
        # =========================
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

        # =========================
        # SUBJECT
        # =========================
        if stack and stack[-1]["level"] == "semester":

            semester_id = get_semester_id(stack[0]["major_id"], stack[-1]["semester"])
            subjects = get_subjects(semester_id)

            for s in subjects:
                if text == s[1]:
                    stack.append({"level": "subject", "subject_id": s[0]})
                    bot.send_message(chat_id, "Choose Type:", reply_markup=categories_keyboard())
                    return

        # =========================
        # CATEGORY
        # =========================
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
# TITLE SELECTION
# =========================

def handle_title_selection(chat_id, number):

    data = resource_state.get(chat_id)
    if not data:
        return

    idx = number - 1
    titles = data["titles"]

    if idx < 0 or idx >= len(titles):
        global_bot.send_message(chat_id, "Invalid number.")
        return

    title = titles[idx]
    items = data["grouped"][title]

    global_bot.send_message(chat_id, f"📘 {data['title_map'][title]}")

    for file_id, year, season in items:
        global_bot.send_document(
            chat_id,
            file_id,
            caption=f"{(season or 'Unknown').capitalize()} {year or 'Unknown'}"
        )


# =========================
# PAGINATION UI (EDIT MESSAGE)
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

    message_id = data.get("message_id")

    try:
        if message_id:
            global_bot.edit_message_text(text, chat_id, message_id)
        else:
            sent = global_bot.send_message(chat_id, text)
            data["message_id"] = sent.message_id
    except:
        sent = global_bot.send_message(chat_id, text)
        data["message_id"] = sent.message_id