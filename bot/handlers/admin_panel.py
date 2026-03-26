from bot.config import ADMINS, SUPER_ADMINS
from bot.keyboards.admin_panel_keyboard import admin_menu, majors_menu, subjects_menu
from bot.database.queries.majors import add_major, get_majors, delete_major, update_major
from bot.database.queries.subjects import add_subject, get_subjects_by_major, delete_subject, update_subject
from bot.database.queries.semesters import get_semester_id, add_semester, delete_semester
from bot.database.queries.resources import add_resource, delete_resource, get_resources, update_resource
from bot.database.queries.admins import add_admin, delete_admin, get_admins
from bot.database.connection import get_connection
from bot.utils.pagination import paginate, pagination_keyboard
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

admin_state = {}
admin_history = {}
RESOURCE_TYPES = ["exam", "books & lectures", "other resources"]

# ---------------------- HELPERS ----------------------
def push_history(chat_id, keyboard):
    if chat_id not in admin_history:
        admin_history[chat_id] = []
    admin_history[chat_id].append(keyboard)

def is_super_admin(user_id):
    return user_id in SUPER_ADMINS

def is_sub_admin(user_id):
    return user_id in ADMINS

def get_user_type(user_id):
    if is_super_admin(user_id):
        return "super"
    if is_sub_admin(user_id):
        return "sub"
    return None

# ---------------------- MAIN PANEL ----------------------
def register_admin_panel(bot):

    @bot.message_handler(func=lambda m: m.text == "⚙️ Admin Panel")
    def admin_panel(message):
        if not get_user_type(message.from_user.id):
            return

        push_history(message.chat.id, admin_menu)
        bot.send_message(message.chat.id, "Admin Panel:", reply_markup=admin_menu())

    # ---------------------- MAJORS ----------------------
    @bot.message_handler(func=lambda m: m.text == "Manage Majors")
    def open_major_menu(message):
        push_history(message.chat.id, majors_menu)
        bot.send_message(message.chat.id, "Majors Management", reply_markup=majors_menu())

    @bot.message_handler(func=lambda m: m.text == "Add Major")
    def add_major_flow(message):
        admin_state[message.chat.id] = {"action": "major_name"}
        bot.send_message(message.chat.id, "Send major name:")

    @bot.message_handler(func=lambda m: admin_state.get(m.chat.id, {}).get("action") == "major_name")
    def get_major_name(message):
        admin_state[message.chat.id]["name"] = message.text
        admin_state[message.chat.id]["action"] = "start_sem"
        bot.send_message(message.chat.id, "Enter start semester (e.g. 1):")

    @bot.message_handler(func=lambda m: admin_state.get(m.chat.id, {}).get("action") == "start_sem")
    def get_start_sem(message):
        try:
            admin_state[message.chat.id]["start"] = int(message.text)
            admin_state[message.chat.id]["action"] = "end_sem"
            bot.send_message(message.chat.id, "Enter end semester (e.g. 8):")
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
            cur.execute("INSERT INTO majors (name) VALUES (%s) RETURNING id", (state["name"],))
            major_id = cur.fetchone()[0]
            for i in range(state["start"], end + 1):
                cur.execute("INSERT INTO semesters (major_id, number) VALUES (%s,%s)", (major_id, i))
            conn.commit()
            cur.close()
            conn.close()
            admin_state.pop(message.chat.id)
            bot.send_message(message.chat.id, "Major created successfully.")
        except ValueError:
            bot.send_message(message.chat.id, "Enter a valid number.")

    # ---------------------- EDIT MAJOR ----------------------
    @bot.message_handler(func=lambda m: m.text == "Edit Major")
    def edit_major_menu(message):
        majors = get_majors()
        markup = InlineKeyboardMarkup()
        for major in majors:
            markup.add(InlineKeyboardButton(major[1], callback_data=f"edit_major:{major[0]}"))
        bot.send_message(message.chat.id, "Select major to edit:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("edit_major"))
    def edit_major_selected(call):
        major_id = int(call.data.split(":")[1])
        admin_state[call.message.chat.id] = {"action": "choose_major_edit", "major_id": major_id}
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Edit Name", callback_data=f"edit_major_name:{major_id}"))
        markup.add(InlineKeyboardButton("Edit Semesters", callback_data=f"edit_major_sem:{major_id}"))
        bot.send_message(call.message.chat.id, "What do you want to edit?", reply_markup=markup)

    # Rename major
    @bot.callback_query_handler(func=lambda c: c.data.startswith("edit_major_name"))
    def edit_major_name(call):
        major_id = int(call.data.split(":")[1])
        admin_state[call.message.chat.id]["action"] = "rename_major"
        bot.send_message(call.message.chat.id, "Send new major name:")

    @bot.message_handler(func=lambda m: admin_state.get(m.chat.id, {}).get("action") == "rename_major")
    def rename_major(message):
        state = admin_state[message.chat.id]
        update_major(state["major_id"], name=message.text)
        admin_state.pop(message.chat.id)
        bot.send_message(message.chat.id, "Major name updated.")

    # Edit semester count
    @bot.callback_query_handler(func=lambda c: c.data.startswith("edit_major_sem"))
    def edit_major_sem(call):
        major_id = int(call.data.split(":")[1])
        admin_state[call.message.chat.id]["action"] = "edit_major_sem"
        bot.send_message(call.message.chat.id, "Send new end semester number:")

    @bot.message_handler(func=lambda m: admin_state.get(m.chat.id, {}).get("action") == "edit_major_sem")
    def finish_edit_major_sem(message):
        state = admin_state[message.chat.id]
        new_end = int(message.text)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT MIN(number), MAX(number) FROM semesters WHERE major_id=%s", (state["major_id"],))
        start, old_end = cur.fetchone()
        if new_end < start:
            bot.send_message(message.chat.id, "End semester cannot be less than start semester.")
            return
        # Delete extra semesters/resources if shrinking
        if new_end < old_end:
            for sem in range(new_end + 1, old_end + 1):
                cur.execute("SELECT id FROM semesters WHERE major_id=%s AND number=%s", (state["major_id"], sem))
                sem_id = cur.fetchone()[0]
                cur.execute("DELETE FROM resources WHERE subject_id IN (SELECT id FROM subjects WHERE semester_id=%s)", (sem_id,))
                cur.execute("DELETE FROM subjects WHERE semester_id=%s", (sem_id,))
                cur.execute("DELETE FROM semesters WHERE id=%s", (sem_id,))
        # Add new semesters if expanding
        elif new_end > old_end:
            for sem in range(old_end + 1, new_end + 1):
                cur.execute("INSERT INTO semesters (major_id, number) VALUES (%s,%s)", (state["major_id"], sem))
        conn.commit()
        cur.close()
        conn.close()
        admin_state.pop(message.chat.id)
        bot.send_message(message.chat.id, "Major semesters updated.")

    # ---------------------- SUBJECTS ----------------------
    @bot.message_handler(func=lambda m: m.text == "Manage Subjects")
    def open_subject_menu(message):
        push_history(message.chat.id, subjects_menu)
        bot.send_message(message.chat.id, "Subjects Management", reply_markup=subjects_menu())

    @bot.message_handler(func=lambda m: m.text == "Edit Subject")
    def edit_subject_menu(message):
        majors = get_majors()
        markup = InlineKeyboardMarkup()
        for major in majors:
            markup.add(InlineKeyboardButton(major[1], callback_data=f"edit_sub_major:{major[0]}"))
        bot.send_message(message.chat.id, "Select major:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("edit_sub_major"))
    def edit_sub_major_selected(call):
        major_id = int(call.data.split(":")[1])
        subjects = get_subjects_by_major(major_id)
        markup = InlineKeyboardMarkup()
        for sub in subjects:
            markup.add(InlineKeyboardButton(sub[1], callback_data=f"edit_subject:{sub[0]}"))
        bot.send_message(call.message.chat.id, "Select subject to edit:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("edit_subject"))
    def edit_subject_name(call):
        subject_id = int(call.data.split(":")[1])
        admin_state[call.message.chat.id] = {"action": "rename_subject", "subject_id": subject_id}
        bot.send_message(call.message.chat.id, "Send new subject name:")

    @bot.message_handler(func=lambda m: admin_state.get(m.chat.id, {}).get("action") == "rename_subject")
    def rename_subject(message):
        state = admin_state[message.chat.id]
        update_subject(state["subject_id"], name=message.text)
        admin_state.pop(message.chat.id)
        bot.send_message(message.chat.id, "Subject updated successfully.")

    # ---------------------- RESOURCES ----------------------
    @bot.message_handler(func=lambda m: m.text == "View Resources")
    def view_resources(message):
        majors = get_majors()
        markup = InlineKeyboardMarkup()
        for major in majors:
            markup.add(InlineKeyboardButton(major[1], callback_data=f"view_res_major:{major[0]}"))
        bot.send_message(message.chat.id, "Select Major:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("view_res_major"))
    def view_res_major(call):
        major_id = int(call.data.split(":")[1])
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT subjects.id, subjects.name
            FROM subjects
            JOIN semesters ON subjects.semester_id = semesters.id
            WHERE semesters.major_id=%s
        """, (major_id,))
        subjects = cur.fetchall()
        cur.close()
        conn.close()
        for sub in subjects:
            res_markup = InlineKeyboardMarkup()
            resources = get_resources(sub[0])
            for r in resources:
                res_markup.add(InlineKeyboardButton(f"{r[1]} ({r[4]} {r[5]})", callback_data=f"view_res_detail:{r[0]}"))
            bot.send_message(call.message.chat.id, f"📚 {sub[1]}", reply_markup=res_markup)

    # ---------------------- BACK ----------------------
    @bot.message_handler(func=lambda m: m.text == "⬅ Back")
    def go_back(message):
        chat_id = message.chat.id
        if chat_id not in admin_history or len(admin_history[chat_id]) <= 1:
            from bot.keyboards.main_menu_keyboard import main_menu
            is_admin = message.from_user.id in ADMINS
            bot.send_message(chat_id, "Main Menu", reply_markup=main_menu(is_admin))
            return
        admin_history[chat_id].pop()
        previous_keyboard = admin_history[chat_id][-1]
        bot.send_message(chat_id, "Going back...", reply_markup=previous_keyboard())