import re

from telebot.types import ReplyKeyboardMarkup
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
# MAIN REGISTER FUNCTION
# =========================

def register_syllabus(bot):

    # ===== Register Callbacks FIRST =====
    # Removed inline button callbacks

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

    # ===== Handle title number selection =====
    @bot.message_handler(func=lambda m: m.text and m.text.isdigit() and resource_state.get(m.chat.id, {}).get("viewing_titles"))
    def handle_title_number(message):
        chat_id = message.chat.id
        data = resource_state.get(chat_id)

        if not data or not data.get("viewing_titles"):
            return

        try:
            title_number = int(message.text) - 1  # Convert to 0-based index
            titles = data.get("titles", [])

            if title_number < 0 or title_number >= len(titles):
                bot.send_message(chat_id, f"Please send a number between 1 and {len(titles)}.")
                return

            title = titles[title_number]
            print(f"[DEBUG] User selected title number {message.text}: {title}")

            # Send files directly for this title (newer to older)
            items = data.get("grouped", {}).get(title)
            if not items:
                bot.send_message(chat_id, "No files found for this title.")
                return

            # Sort items from newer to older (already sorted in resource_state)
            # Send each document
            display_title = data['title_map'].get(title, title)
            bot.send_message(chat_id, f"📘 Sending files for: {display_title}")

            sent_count = 0
            for file_id, year, season in items:
                try:
                    display_season = (season or 'Unknown').capitalize()
                    display_year = year or 'Unknown'
                    caption = f"{display_season} {display_year}"
                    bot.send_document(chat_id, file_id, caption=caption)
                    sent_count += 1
                except Exception as e:
                    print(f"[ERROR] Failed to send document {file_id}: {e}")

            if sent_count == 0:
                bot.send_message(chat_id, "Failed to send any files.")
            else:
                bot.send_message(chat_id, f"✅ Sent {sent_count} file(s). Send another number to view more resources, or /back to menu.")

        except Exception as e:
            print(f"[ERROR] handle_title_number failed: {e}")
            bot.send_message(chat_id, "Invalid input. Please send a valid number.")

    # ===== Command Handlers for Pagination =====
    @bot.message_handler(func=lambda m: m.text == "/prev" and resource_state.get(m.chat.id, {}).get("viewing_titles"))
    def handle_prev(message):
        chat_id = message.chat.id
        data = resource_state.get(chat_id)
        if not data:
            return
        current_page = data.get("current_page", 0)
        if current_page > 0:
            send_titles_page(chat_id, current_page - 1)
        else:
            bot.send_message(chat_id, "Already on the first page.")

    @bot.message_handler(func=lambda m: m.text == "/next" and resource_state.get(m.chat.id, {}).get("viewing_titles"))
    def handle_next(message):
        chat_id = message.chat.id
        data = resource_state.get(chat_id)
        if not data:
            return
        current_page = data.get("current_page", 0)
        titles = data.get("titles", [])
        total_pages = (len(titles) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        if current_page + 1 < total_pages:
            send_titles_page(chat_id, current_page + 1)
        else:
            bot.send_message(chat_id, "Already on the last page.")


    @bot.message_handler(func=lambda m: m.text == "⬅ Back")
    def syllabus_back_button(message):
        chat_id = message.chat.id

        # 🚀 If viewing titles → go back to categories
        if resource_state.get(chat_id, {}).get("viewing_titles"):

            resource_state[chat_id]["viewing_titles"] = False

            state = user_state.get(chat_id, {})
            stack = state.get("stack", [])

            for item in reversed(stack):
                if item["level"] == "subject":

                    markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    markup.add("Exam", "Books & Lectures", "Other Resources")
                    markup.add("⬅ Back")

                    bot.send_message(chat_id, "Choose Type:", reply_markup=markup)
                    return

        # 🚀 Otherwise normal back
        _syllabus_go_back(chat_id, message.from_user.id)


    def _syllabus_go_back(chat_id, user_id):

        state = user_state.get(chat_id, {})
        stack = state.get("stack", [])

        # ❌ Nothing in stack → main menu
        if not stack:
            from bot.keyboards.main_menu_keyboard import main_menu
            bot.send_message(chat_id, "Main Menu", reply_markup=main_menu(user_id in ADMINS))
            return

        # Remove current level
        stack.pop()

        # ❌ Stack empty after pop → main menu
        if not stack:
            from bot.keyboards.main_menu_keyboard import main_menu
            bot.send_message(chat_id, "Main Menu", reply_markup=main_menu(user_id in ADMINS))
            return

        last = stack[-1]

        # =========================
        # REBUILD UI FROM STATE
        # =========================

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

            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("Exam", "Books & Lectures", "Other Resources")
            markup.add("⬅ Back")

            bot.send_message(chat_id, "Choose Type:", reply_markup=markup)

    @bot.message_handler(commands=['back'])
    def handle_back(message):
        chat_id = message.chat.id

        # 🚀 CASE 1: If viewing titles → go back to categories
        if resource_state.get(chat_id, {}).get("viewing_titles"):

            resource_state[chat_id]["viewing_titles"] = False

            state = user_state.get(chat_id, {})
            stack = state.get("stack", [])

            # Find subject level in stack
            for item in reversed(stack):
                if item["level"] == "subject":
                    
                    markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    markup.add("Exam", "Books & Lectures", "Other Resources")
                    markup.add("⬅ Back")

                    bot.send_message(chat_id, "Choose Type:", reply_markup=markup)
                    return

        # 🚀 CASE 2: Normal back
        _syllabus_go_back(chat_id, message.from_user.id)

    # ===== Navigation =====
    @bot.message_handler(func=lambda m: True, content_types=['text'])
    def navigation(message):

        chat_id = message.chat.id
        text = message.text.strip()

        print(f"[NAVIGATION] {text}")

        # Block navigation when viewing titles
        if resource_state.get(chat_id, {}).get("viewing_titles"):
            return

        if text == "📚 Syllabus":
            return

        state = user_state.setdefault(chat_id, {})
        stack = state.setdefault("stack", [])

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

            sem_number = int(text.split()[1])
            major_id = stack[-1]["major_id"]

            stack.append({
                "level": "semester",
                "semester": sem_number
            })

            semester_id = get_semester_id(major_id, sem_number)
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

            major_id = stack[0]["major_id"]
            semester = stack[-1]["semester"]

            semester_id = get_semester_id(major_id, semester)
            subjects = get_subjects(semester_id)

            for s in subjects:
                if text == s[1]:

                    stack.append({
                        "level": "subject",
                        "subject_id": s[0]
                    })

                    markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    markup.add("Exam", "Books & Lectures", "Other Resources")
                    markup.add("⬅ Back")

                    bot.send_message(chat_id, "Choose Type:", reply_markup=markup)
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

            stack.append({
                "level": "category",
                "category": category
            })

            resources = get_resources(subject_id, category)

            if not resources:
                bot.send_message(chat_id, "No resources found.")
                return

            try:
                grouped = {}
                title_map = {}

                for title, file_id, year, season in resources:
                    if not title or not file_id:
                        continue

                    clean = normalize(title)
                    year = year or 0
                    season = season or ''

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
                    "title_map": title_map,
                    "viewing_titles": True
                }

                send_titles_page(chat_id, 0)

            except Exception as e:
                print(f"[ERROR] Resource processing failed: {e}")
                bot.send_message(chat_id, "Error processing resources.")

            return

        

# =========================
# UI FUNCTIONS
# =========================

def send_titles_page(chat_id, page, message_id=None):

    data = resource_state.get(chat_id)
    if not data:
        print(f"[ERROR] send_titles_page: no data for chat_id {chat_id}")
        return

    titles = data.get("titles", [])
    print(f"[DEBUG] send_titles_page: {len(titles)} titles, page {page}")

    if not titles:
        print("[DEBUG] No titles to display")
        return

    page_items = paginate(titles, page)

    # Create numbered text list
    text_lines = []
    for index, title in enumerate(page_items):
        global_index = page * ITEMS_PER_PAGE + index + 1  # 1-based numbering
        display = data["title_map"].get(title, title)
        text_lines.append(f"{global_index}. {display}")

    page_text = "\n".join(text_lines)

    total_pages = (len(titles) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    current_page = page + 1

    full_text = f"📚 Page {current_page}/{total_pages}:\n\n{page_text}\n\nSend the number of the title you want to view its resources.\n\nCommands: ⬅️ /prev    -    ➡️ /next \n🔙 /back to menu"

    # Update current page in state
    resource_state[chat_id]["current_page"] = page

    # Determine target message id for editing (if possible)
    if message_id:
        resource_state[chat_id]["last_message_id"] = message_id
    else:
        message_id = resource_state[chat_id].get("last_message_id")

    try:
        if message_id:
            global_bot.edit_message_text(
                full_text,
                chat_id,
                message_id
            )
            resource_state[chat_id]["last_message_id"] = message_id
            print("[DEBUG] send_titles_page: edited message")
        else:
            sent = global_bot.send_message(
                chat_id,
                full_text
            )
            resource_state[chat_id]["last_message_id"] = sent.message_id
            print("[DEBUG] send_titles_page: sent new message")
    except Exception as e:
        print(f"[ERROR] send_titles_page failed: {e}")
        global_bot.send_message(chat_id, f"Error displaying titles: {e}")