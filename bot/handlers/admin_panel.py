from bot.config import ADMINS
from bot.keyboards.admin_panel_keyboard import admin_menu, majors_menu, subjects_menu
from bot.database.queries.majors import add_major, get_majors, delete_major, update_major
from bot.database.queries.subjects import add_subject, get_subjects, delete_subject
from bot.database.queries.semesters import get_semester_id
from bot.database.queries.resources import add_resource, delete_resource
from bot.database.connection import get_connection
from bot.utils.pagination import paginate, pagination_keyboard
from bot.handlers.share import share_state
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.types import ReplyKeyboardMarkup, KeyboardButton



admin_state = {}
admin_history = {}

RESOURCE_TYPES = [
    "exam",
    "books & lectures",
    "other resources"
]



# Helper function for the back button
def push_history(chat_id, keyboard):
    if chat_id not in admin_history:
        admin_history[chat_id] = []
    admin_history[chat_id].append(keyboard)




def register_admin_panel(bot):

    @bot.message_handler(func=lambda m: m.text == "⚙️ Admin Panel" and m.chat.id not in share_state)
    def admin_panel(message):

        if message.from_user.id not in ADMINS:
            return
        
        push_history(message.chat.id, admin_menu)

        bot.send_message(
            message.chat.id,
            "Admin Panel:",
            reply_markup=admin_menu()
        )


    @bot.message_handler(func=lambda m: m.text == "Manage Majors")
    def open_major_menu(message):

        push_history(message.chat.id, majors_menu)

        bot.send_message(
            message.chat.id,
            "Majors Management",
            reply_markup=majors_menu()
        )


    @bot.message_handler(func=lambda m: m.text == "Manage Subjects")
    def open_subject_menu(message):

        push_history(message.chat.id, subjects_menu)

        bot.send_message(
            message.chat.id,
            "Subjects Management",
            reply_markup=subjects_menu()
        )

    @bot.message_handler(func=lambda m: m.text == "Manage Resources")
    def manage_resources(message):

        markup = ReplyKeyboardMarkup(resize_keyboard=True)

        markup.add("Upload Resource")
        markup.add("View Resources")
        markup.add("Delete Resource")

        markup.add("⬅ Back")

        push_history(message.chat.id, lambda: markup)

        bot.send_message(
            message.chat.id,
            "Resources Management",
            reply_markup=markup
        )


    @bot.message_handler(func=lambda m: m.text == "Add Major")
    def start_add_major(message):
        admin_state[message.chat.id] = {"action": "major_name"}
        bot.send_message(message.chat.id, "Send major name:")


    @bot.message_handler(func=lambda m: admin_state.get(m.chat.id, {}).get("action") == "major_name")
    def get_major_name(message):
        admin_state[message.chat.id]["name"] = message.text
        admin_state[message.chat.id]["action"] = "start_sem"

        bot.send_message(message.chat.id, "Enter START semester (e.g. 1):")


    @bot.message_handler(func=lambda m: admin_state.get(m.chat.id, {}).get("action") == "start_sem")
    def get_start_sem(message):
        try:
            admin_state[message.chat.id]["start"] = int(message.text)
            admin_state[message.chat.id]["action"] = "end_sem"

            bot.send_message(message.chat.id, "Enter END semester (e.g. 8):")
        except ValueError:
            bot.send_message(message.chat.id, "Enter a valid number.")


    @bot.message_handler(func=lambda m: admin_state.get(m.chat.id, {}).get("action") == "end_sem")
    def finish_major(message):

        try:
            state = admin_state[message.chat.id]
            end = int(message.text)

            if end < state["start"]:
                bot.send_message(message.chat.id, "End must be >= start.")
                return

            conn = get_connection()
            cur = conn.cursor()

            cur.execute(
                "INSERT INTO majors (name) VALUES (%s) RETURNING id",
                (state["name"],)
            )
            major_id = cur.fetchone()[0]

            for i in range(state["start"], end + 1):
                cur.execute(
                    "INSERT INTO semesters (major_id, number) VALUES (%s,%s)",
                    (major_id, i)
                )

            conn.commit()
            cur.close()
            conn.close()

            admin_state.pop(message.chat.id)

            bot.send_message(message.chat.id, "Major created successfully.")

        except ValueError:
            bot.send_message(message.chat.id, "Enter a valid number.")


    @bot.message_handler(func=lambda m: m.text == "Edit Major")
    def edit_major_menu(message):

        majors = get_majors()

        markup = InlineKeyboardMarkup()

        for major in majors:

            markup.add(
                InlineKeyboardButton(
                    major[1],
                    callback_data=f"edit_major:{major[0]}"
                )
            )

        bot.send_message(
            message.chat.id,
            "Select major to edit:",
            reply_markup=markup
        )


    @bot.callback_query_handler(func=lambda c: c.data.startswith("edit_major"))
    def edit_major_selected(call):

        major_id = call.data.split(":")[1]

        admin_state[call.message.chat.id] = {
            "action": "rename_major",
            "major_id": major_id
        }

        bot.send_message(
            call.message.chat.id,
            "Send the new name:"
        )


    @bot.message_handler(func=lambda m: admin_state.get(m.chat.id, {}).get("action") == "rename_major")
    def rename_major(message):

        state = admin_state[message.chat.id]

        update_major(state["major_id"], message.text)

        admin_state.pop(message.chat.id)

        bot.send_message(
            message.chat.id,
            "Major updated."
        )


    def build_major_markup(majors, page):
        page_items = paginate(majors, page)

        markup = InlineKeyboardMarkup()

        for major in page_items:
            markup.add(
                InlineKeyboardButton(
                    major[1],
                    callback_data=f"delete_major:{major[0]}"
                )
            )

        nav = pagination_keyboard("majors", page, len(majors))
        if nav.keyboard:
            for row in nav.keyboard:
                markup.row(*row)

        return markup


    def show_major_page(bot, chat_id, majors, page):
        markup = build_major_markup(majors, page)
        bot.send_message(chat_id, "Choose major to delete:", reply_markup=markup)


    def build_subjects_markup(major_id, subjects, page):
        page_items = paginate(subjects, page)

        markup = InlineKeyboardMarkup()

        for subject in page_items:
            markup.add(
                InlineKeyboardButton(
                    subject[1],
                    callback_data=f"del_subject:{subject[0]}"
                )
            )

        nav = pagination_keyboard(f"subjects_page:{major_id}", page, len(subjects))
        if nav.keyboard:
            for row in nav.keyboard:
                markup.row(*row)

        return markup


    @bot.message_handler(func=lambda m: m.text == "Delete Major")
    def delete_major_menu(message):

        majors = get_majors()
        show_major_page(bot, message.chat.id, majors, 0)


    @bot.callback_query_handler(func=lambda c: c.data.startswith("delete_major"))
    def delete_major_handler(call):

        major_id = call.data.split(":")[1]

        try:
            delete_major(major_id)
            bot.answer_callback_query(call.id, "Major deleted")
        except Exception as e:
            bot.answer_callback_query(call.id, "Error deleting")
            bot.send_message(call.message.chat.id, str(e))
            return

        majors = get_majors()

        markup = build_major_markup(majors, 0)

        bot.edit_message_text(
            "Choose major to delete:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )


    @bot.callback_query_handler(func=lambda c: c.data.startswith("majors_page"))
    def majors_page_handler(call):

        parts = call.data.split(":")
        try:
            page = int(parts[-1])
        except (ValueError, IndexError):
            return

        majors = get_majors()

        if page < 0 or page * 5 >= len(majors):
            return

        markup = build_major_markup(majors, page)

        bot.edit_message_text(
            "Choose major to delete:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )


    @bot.callback_query_handler(func=lambda c: c.data.startswith("subjects_page"))
    def subjects_page_handler(call):

        parts = call.data.split(":")
        if len(parts) < 3:
            return

        try:
            major_id = int(parts[1])
            page = int(parts[-1])
        except ValueError:
            return

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT subjects.id, subjects.name
            FROM subjects
            JOIN semesters ON subjects.semester_id = semesters.id
            WHERE semesters.major_id = %s
        """, (major_id,))

        subjects = cur.fetchall()

        cur.close()
        conn.close()

        if page < 0 or page * 5 >= len(subjects):
            return

        markup = build_subjects_markup(major_id, subjects, page)

        bot.edit_message_text(
            "Select subject to delete:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )


    @bot.message_handler(func=lambda m: m.text == "Add Subject")
    def start_add_subject(message):

        majors = get_majors()

        markup = InlineKeyboardMarkup()

        for major in majors:

            markup.add(
                InlineKeyboardButton(
                    major[1],
                    callback_data=f"subject_major:{major[0]}"
                )
            )

        bot.send_message(
            message.chat.id,
            "Select Major:",
            reply_markup=markup
        )


    @bot.callback_query_handler(func=lambda c: c.data.startswith("subject_major"))
    def subject_major_selected(call):

        major_id = call.data.split(":")[1]

        admin_state[call.message.chat.id] = {
            "action": "adding_subject",
            "major_id": major_id
        }

        markup = InlineKeyboardMarkup()

        for i in range(1, 9):
            markup.add(
                InlineKeyboardButton(
                    f"Semester {i}",
                    callback_data=f"subject_sem:{i}"
                )
            )

        bot.send_message(
            call.message.chat.id,
            "Choose semester:",
            reply_markup=markup
        )


    @bot.callback_query_handler(func=lambda c: c.data.startswith("subject_sem"))
    def subject_sem_selected(call):

        semester = call.data.split(":")[1]

        state = admin_state.get(call.message.chat.id)

        state["semester"] = semester

        bot.send_message(
            call.message.chat.id,
            "Send subject name:"
        )


    @bot.message_handler(func=lambda m: admin_state.get(m.chat.id, {}).get("action") == "adding_subject")
    def subject_name_received(message):

        state = admin_state[message.chat.id]

        semester_id = get_semester_id(state["major_id"], int(state["semester"]))

        add_subject(
            semester_id=semester_id,
            name=message.text
        )

        admin_state.pop(message.chat.id)

        bot.send_message(
            message.chat.id,
            "Subject added successfully."
        )


    @bot.message_handler(func=lambda m: m.text == "Delete Subject")
    def delete_subject_menu(message):

        majors = get_majors()

        markup = InlineKeyboardMarkup()

        for major in majors:
            markup.add(
                InlineKeyboardButton(
                    major[1],
                    callback_data=f"del_subject_major:{major[0]}"
                )
            )

        bot.send_message(
            message.chat.id,
            "Select major:",
            reply_markup=markup
        )


    @bot.callback_query_handler(func=lambda c: c.data.startswith("del_subject_major"))
    def del_subject_major_selected(call):

        major_id = int(call.data.split(":")[1])

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT subjects.id, subjects.name
            FROM subjects
            JOIN semesters ON subjects.semester_id = semesters.id
            WHERE semesters.major_id = %s
        """, (major_id,))

        subjects = cur.fetchall()

        cur.close()
        conn.close()

        markup = build_subjects_markup(major_id, subjects, 0)

        bot.send_message(
            call.message.chat.id,
            "Select subject to delete:",
            reply_markup=markup
        )


    @bot.callback_query_handler(func=lambda c: c.data.startswith("del_subject"))
    def del_subject_handler(call):

        subject_id = call.data.split(":")[1]

        delete_subject(subject_id)

        bot.answer_callback_query(call.id, "Subject deleted")

        bot.edit_message_text(
            "Subject deleted.",
            call.message.chat.id,
            call.message.message_id
        )





    @bot.message_handler(func=lambda m: m.text == "Upload Resource")
    def start_upload(message):

        majors = get_majors()

        markup = InlineKeyboardMarkup()

        for major in majors:
            markup.add(
                InlineKeyboardButton(
                    major[1],
                    callback_data=f"res_major:{major[0]}"
                )
            )

        bot.send_message(
            message.chat.id,
            "Choose major:",
            reply_markup=markup
        )

    @bot.message_handler(content_types=["document", "photo", "video", "audio", "voice", "video_note", "animation", "sticker", "text"])
    def receive_resource(message):
        state = admin_state.get(message.chat.id)

        if not state:
            return

        if message.document:
            file_id = message.document.file_id

        elif message.photo:
            file_id = message.photo[-1].file_id

        elif message.video:
            file_id = message.video.file_id

        elif message.audio:
            file_id = message.audio.file_id

        elif message.voice:
            file_id = message.voice.file_id

        elif message.video_note:
            file_id = message.video_note.file_id

        elif message.animation:
            file_id = message.animation.file_id

        elif message.sticker:
            file_id = message.sticker.file_id

        elif message.text:
            file_id = message.text   # this stores links or plain text

        else:
            bot.send_message(message.chat.id, "Unsupported type.")
            return

        state["file_id"] = file_id

        bot.send_message(
            message.chat.id,
            "Enter academic year (example: 2023):"
        )


    @bot.callback_query_handler(func=lambda c: c.data.startswith("res_major"))
    def res_major_selected(call):

        major_id = call.data.split(":")[1]

        admin_state[call.message.chat.id] = {
            "action": "uploading_resource_setup",
            "major_id": major_id
        }

        markup = InlineKeyboardMarkup()

        for i in range(1, 9):
            markup.add(
                InlineKeyboardButton(
                    f"Semester {i}",
                    callback_data=f"res_sem:{i}"
                )
            )

        bot.send_message(
            call.message.chat.id,
            "Choose semester:",
            reply_markup=markup
        )


    @bot.callback_query_handler(func=lambda c: c.data.startswith("res_sem"))
    def res_sem_selected(call):

        semester = call.data.split(":")[1]

        state = admin_state.get(call.message.chat.id)

        state["semester"] = semester

        semester_id = get_semester_id(
            state["major_id"],
            int(state["semester"])
        )

        subjects = get_subjects(semester_id)

        markup = InlineKeyboardMarkup()

        for subject in subjects:
            markup.add(
                InlineKeyboardButton(
                    subject[1],
                    callback_data=f"res_subject:{subject[0]}"
                )
            )

        bot.send_message(
            call.message.chat.id,
            "Choose subject:",
            reply_markup=markup
        )


    

    @bot.callback_query_handler(func=lambda c: c.data.startswith("res_subject"))
    def res_subject_selected(call):

        subject_id = call.data.split(":")[1]

        state = admin_state.get(call.message.chat.id)

        state["subject_id"] = subject_id

        markup = InlineKeyboardMarkup()

        for category in RESOURCE_TYPES:
            display_name = category.replace(" & ", " & ").title()  # "exam" -> "Exam", "books & lectures" -> "Books & Lectures"
            markup.add(
                InlineKeyboardButton(
                    display_name,
                    callback_data=f"res_cat:{category}"
                )
            )

        bot.send_message(
            call.message.chat.id,
            "Choose resource category:",
            reply_markup=markup
        )


    @bot.callback_query_handler(func=lambda c: c.data.startswith("res_cat"))
    def res_cat_selected(call):

        category = call.data.split(":", 1)[1].lower()  # Normalize to lowercase

        state = admin_state.get(call.message.chat.id)

        state["category"] = category
        state["action"] = "uploading_resource"

        bot.send_message(
            call.message.chat.id,
            "Send the resource file:"
        )


    @bot.message_handler(func=lambda m: admin_state.get(m.chat.id, {}).get("action") == "uploading_resource" and "file_id" in admin_state.get(m.chat.id, {}) and "year" not in admin_state.get(m.chat.id, {}))
    def receive_year(message):

        try:
            year = int(message.text)
        except ValueError:
            bot.send_message(message.chat.id, "Please enter a valid year (number):")
            return

        state = admin_state[message.chat.id]
        state["year"] = year

        bot.send_message(
            message.chat.id,
            "Enter season (fall/spring/summer):"
        )


    @bot.message_handler(func=lambda m: admin_state.get(m.chat.id, {}).get("action") == "uploading_resource" and "year" in admin_state.get(m.chat.id, {}) and "season" not in admin_state.get(m.chat.id, {}))
    def receive_season(message):

        season = message.text.lower()
        if season not in ["fall", "spring", "summer"]:
            bot.send_message(message.chat.id, "Please enter fall, spring, or summer:")
            return

        state = admin_state[message.chat.id]
        state["season"] = season

        bot.send_message(
            message.chat.id,
            "Enter resource title:"
        )


    @bot.message_handler(func=lambda m: admin_state.get(m.chat.id, {}).get("action") == "uploading_resource" and "season" in admin_state.get(m.chat.id, {}) and "title" not in admin_state.get(m.chat.id, {}))
    def receive_title(message):

        state = admin_state[message.chat.id]
        state["title"] = message.text

        add_resource(
            subject_id=state["subject_id"],
            category=state["category"],
            title=state["title"],
            file_id=state["file_id"],
            year=state["year"],
            season=state["season"]
        )

        admin_state.pop(message.chat.id)

        bot.send_message(
            message.chat.id,
            "Resource uploaded successfully."
        )

    

    @bot.message_handler(func=lambda m: m.text == "View Resources")
    def view_resources(message):
        bot.send_message(message.chat.id, "Feature coming soon.")




    @bot.message_handler(func=lambda m: m.text == "⬅ Back")
    def go_back(message):

        chat_id = message.chat.id

        if chat_id not in admin_history or len(admin_history[chat_id]) <= 1:
            from bot.keyboards.main_menu_keyboard import main_menu
            is_admin = message.from_user.id in ADMINS

            bot.send_message(
                chat_id,
                "Main Menu",
                reply_markup=main_menu(is_admin)
            )
            return

        admin_history[chat_id].pop()
        previous_keyboard = admin_history[chat_id][-1]

        bot.send_message(
            chat_id,
            "Going back...",
            reply_markup=previous_keyboard()
        )


    def build_resources_markup(resources, page):
        page_items = paginate(resources, page)

        markup = InlineKeyboardMarkup()

        for r in page_items:
            markup.add(
                InlineKeyboardButton(
                    r[1],
                    callback_data=f"del_res:{r[0]}"
                )
            )

        nav = pagination_keyboard("del_res_page", page, len(resources))
        if nav.keyboard:
            for row in nav.keyboard:
                markup.row(*row)

        return markup


    @bot.message_handler(func=lambda m: m.text == "Delete Resource")
    def delete_resource_menu(message):

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT id, title FROM resources")
        resources = cur.fetchall()

        cur.close()
        conn.close()

        markup = build_resources_markup(resources, 0)

        bot.send_message(message.chat.id, "Choose resource to delete:", reply_markup=markup)


    @bot.callback_query_handler(func=lambda c: c.data.startswith("del_res:"))
    def delete_resource_handler(call):

        resource_id = call.data.split(":")[1]

        delete_resource(resource_id)

        bot.answer_callback_query(call.id, "Resource deleted")

        bot.edit_message_text(
            "Resource deleted.",
            call.message.chat.id,
            call.message.message_id
        )


    @bot.callback_query_handler(func=lambda c: c.data.startswith("del_res_page"))
    def del_res_page_handler(call):

        parts = call.data.split(":")
        try:
            page = int(parts[-1])
        except (ValueError, IndexError):
            return

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT id, title FROM resources")
        resources = cur.fetchall()

        cur.close()
        conn.close()

        if page < 0 or page * 5 >= len(resources):
            return

        markup = build_resources_markup(resources, page)

        bot.edit_message_text(
            "Choose resource to delete:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )