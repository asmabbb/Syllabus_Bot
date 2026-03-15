from bot.config import ADMINS
from bot.keyboards.admin_panel_keyboard import admin_menu, majors_menu, subjects_menu
from bot.database.queries.majors import add_major, get_majors, delete_major, update_major
from bot.database.queries.subjects import add_subject, get_subjects, delete_subject
from bot.database.queries.semesters import get_semester_id
from bot.database.queries.resources import add_resource
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

admin_state = {}

RESOURCE_TYPES = [
    "Exam",
    "Books & Lectures",
    "Other Resources"
]


def register_admin_panel(bot):

    @bot.message_handler(func=lambda m: m.text == "⚙️ Admin Panel")
    def admin_panel(message):

        if message.from_user.id not in ADMINS:
            return

        bot.send_message(
            message.chat.id,
            "Admin Panel:",
            reply_markup=admin_menu()
        )


    @bot.message_handler(func=lambda m: m.text == "Manage Majors")
    def open_major_menu(message):

        bot.send_message(
            message.chat.id,
            "Majors Management",
            reply_markup=majors_menu()
        )


    @bot.message_handler(func=lambda m: m.text == "Manage Subjects")
    def subject_menu(message):

        bot.send_message(
            message.chat.id,
            "Subjects Management",
            reply_markup=subject_menu()
        )


    @bot.message_handler(func=lambda m: m.text == "Manage Resources")
    def manage_resources(message):

        markup = ReplyKeyboardMarkup(resize_keyboard=True)

        markup.add("Upload Resource")
        markup.add("View Resources")
        markup.add("Delete Resource")

        markup.add("⬅ Back")

        bot.send_message(
            message.chat.id,
            "Resources Management",
            reply_markup=markup
        )


    @bot.message_handler(func=lambda m: m.text == "Add Major")
    def start_add_major(message):

        admin_state[message.chat.id] = {"action": "add_major"}

        bot.send_message(
            message.chat.id,
            "Send the new major name."
        )


    @bot.message_handler(func=lambda m: admin_state.get(m.chat.id, {}).get("action") == "add_major")
    def finish_add_major(message):

        add_major(message.text)

        admin_state.pop(message.chat.id)

        bot.send_message(
            message.chat.id,
            "Major added successfully."
        )


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


    @bot.message_handler(func=lambda m: m.text == "Delete Major")
    def delete_major_menu(message):

        majors = get_majors()

        markup = InlineKeyboardMarkup()

        for major in majors:

            markup.add(
                InlineKeyboardButton(
                    major[1],
                    callback_data=f"delete_major:{major[0]}"
                )
            )

        bot.send_message(
            message.chat.id,
            "Choose major to delete:",
            reply_markup=markup
        )


    @bot.callback_query_handler(func=lambda c: c.data.startswith("delete_major"))
    def delete_major_handler(call):

        major_id = call.data.split(":")[1]

        delete_major(major_id)

        bot.answer_callback_query(call.id, "Major deleted")

        majors = get_majors()

        markup = InlineKeyboardMarkup()

        for major in majors:
            markup.add(
                InlineKeyboardButton(
                    major[1],
                    callback_data=f"delete_major:{major[0]}"
                )
            )

        bot.edit_message_text(
            "Choose major to delete:",
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

        for i in range(1, 8):
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

        major_id = call.data.split(":")[1]

        subjects = get_subjects(major_id)

        markup = InlineKeyboardMarkup()

        for subject in subjects:
            markup.add(
                InlineKeyboardButton(
                    subject[1],
                    callback_data=f"del_subject:{subject[0]}"
                )
            )

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


    @bot.message_handler(content_types=["document","photo"])
    def receive_resource(message):

        state = admin_state.get(message.chat.id)

        if not state or state.get("action") != "uploading_resource":
            return

        if message.document:
            file_id = message.document.file_id
        else:
            file_id = message.photo[-1].file_id

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

        for i in range(1, 8):
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

        subjects = get_subjects(state["major_id"])

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
            markup.add(
                InlineKeyboardButton(
                    category,
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

        category = call.data.split(":", 1)[1]  # in case category has :

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

        bot.send_message(
            message.chat.id,
            "Resource uploaded successfully"
        )

    @bot.message_handler(func=lambda m: m.text == "View Resources")
    def view_resources(message):
        bot.send_message(message.chat.id, "Feature coming soon.")