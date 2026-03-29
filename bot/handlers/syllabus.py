import re
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.bot_instance import bot
from bot.database.queries.majors import get_majors
from bot.database.queries.semesters import get_semester_id, get_semesters_by_major
from bot.database.queries.subjects import get_subjects
from bot.database.queries.resources import get_resources
from bot.utils.pagination import paginate, ITEMS_PER_PAGE
from bot.handlers.share import share_state

user_state = {}

# =========================
# HELPERS
# =========================

def normalize(text):
    return re.sub(r'\s+', ' ', text.strip().lower())


def build_keyboard(buttons, back_data=None):
    kb = InlineKeyboardMarkup()
    for text, data in buttons:
        kb.add(InlineKeyboardButton(text, callback_data=data))

    if back_data:
        kb.add(InlineKeyboardButton("⬅ Back", callback_data=back_data))

    return kb


def edit(chat_id, msg_id, text, kb):
    bot.edit_message_text(
        text,
        chat_id,
        msg_id,
        reply_markup=kb
    )


# =========================
# MAIN
# =========================

def register_syllabus(bot):

    # =========================
    # ENTRY
    # =========================
    @bot.message_handler(func=lambda m: m.text == "📚 المناهج" and m.chat.id not in share_state)
    def syllabus(message):

        majors = get_majors()

        buttons = [(m[1], f"major:{m[0]}") for m in majors]

        kb = build_keyboard(buttons)

        sent = bot.send_message(
            message.chat.id,
            "Choose Major:",
            reply_markup=kb
        )

        user_state[message.chat.id] = {
            "message_id": sent.message_id
        }


    # =========================
    # CALLBACK ROUTER (ONLY ONE)
    # =========================
    @bot.callback_query_handler(func=lambda call: True)
    def router(call):

        chat_id = call.message.chat.id
        msg_id = call.message.message_id
        data = call.data

        print("[CALLBACK]", data)

        # =========================
        # MAJOR
        # =========================
        if data.startswith("major:"):
            major_id = int(data.split(":")[1])

            semesters = get_semesters_by_major(major_id)

            buttons = [
                (f"Semester {s}", f"semester:{major_id}:{s}")
                for s in semesters
            ]

            kb = build_keyboard(buttons, back_data="home")

            edit(chat_id, msg_id, "Choose Semester:", kb)


        # =========================
        # SEMESTER
        # =========================
        elif data.startswith("semester:"):
            _, major_id, sem = data.split(":")
            major_id = int(major_id)
            sem = int(sem)

            semester_id = get_semester_id(major_id, sem)
            subjects = get_subjects(semester_id)

            buttons = [
                (s[1], f"subject:{major_id}:{sem}:{s[0]}")
                for s in subjects
            ]

            kb = build_keyboard(buttons, back_data=f"major:{major_id}")

            edit(chat_id, msg_id, "Choose Subject:", kb)


        # =========================
        # SUBJECT
        # =========================
        elif data.startswith("subject:"):
            _, major_id, sem, subject_id = data.split(":")
            major_id, sem, subject_id = int(major_id), int(sem), int(subject_id)

            buttons = [
                ("Exam", f"cat:{major_id}:{sem}:{subject_id}:exam"),
                ("Books & Lectures", f"cat:{major_id}:{sem}:{subject_id}:books"),
                ("Other Resources", f"cat:{major_id}:{sem}:{subject_id}:other"),
            ]

            kb = build_keyboard(buttons, back_data=f"semester:{major_id}:{sem}")

            edit(chat_id, msg_id, "Choose Type:", kb)


        # =========================
        # CATEGORY
        # =========================
        elif data.startswith("cat:"):
            _, major_id, sem, subject_id, category = data.split(":")
            subject_id = int(subject_id)

            mapping = {
                "exam": "exam",
                "books": "books & lectures",
                "other": "other resources"
            }

            resources = get_resources(subject_id, mapping[category])

            if not resources:
                bot.answer_callback_query(call.id, "No resources found.")
                return

            grouped, title_map = {}, {}

            for title, file_id, year, season in resources:
                clean = normalize(title)
                grouped.setdefault(clean, []).append((file_id, year, season))
                title_map[clean] = title

            titles = sorted(grouped.keys())

            user_state[chat_id]["resources"] = {
                "grouped": grouped,
                "titles": titles,
                "title_map": title_map,
                "page": 0,
                "meta": (major_id, sem, subject_id, category)
            }

            send_page(chat_id, msg_id)


        # =========================
        # PAGINATION
        # =========================
        elif data == "next":
            user_state[chat_id]["resources"]["page"] += 1
            send_page(chat_id, msg_id)

        elif data == "prev":
            user_state[chat_id]["resources"]["page"] -= 1
            send_page(chat_id, msg_id)


        # =========================
        # TITLE CLICK
        # =========================
        elif data.startswith("title:"):
            idx = int(data.split(":")[1])

            res = user_state[chat_id]["resources"]
            title = res["titles"][idx]

            for file_id, year, season in res["grouped"][title]:

                caption = f"{(season or '').capitalize()} {year or ''}"

                # LINK
                if file_id.startswith("http"):
                    bot.send_message(chat_id, f"{title}\n{file_id}")

                # PHOTO
                elif file_id.startswith("AgACAg"):
                    bot.send_photo(chat_id, file_id, caption=caption)

                # VIDEO
                elif file_id.startswith("BAACAg"):
                    bot.send_video(chat_id, file_id, caption=caption)

                # AUDIO
                elif file_id.startswith("CQACAg"):
                    bot.send_audio(chat_id, file_id, caption=caption)

                # DEFAULT = DOCUMENT
                else:
                    bot.send_document(chat_id, file_id, caption=caption)

        # =========================
        # BACK
        # =========================
        elif data == "home":
            majors = get_majors()
            buttons = [(m[1], f"major:{m[0]}") for m in majors]
            kb = build_keyboard(buttons)
            edit(chat_id, msg_id, "Choose Major:", kb)


    # =========================
    # PAGE RENDER
    # =========================
    def send_page(chat_id, msg_id):

        data = user_state[chat_id]["resources"]

        titles = data["titles"]
        page = data["page"]

        total = (len(titles) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        page = max(0, min(page, total - 1))
        data["page"] = page

        page_items = paginate(titles, page)

        buttons = []
        for i, t in enumerate(page_items):
            idx = page * ITEMS_PER_PAGE + i
            buttons.append((data["title_map"][t], f"title:{idx}"))

        # pagination buttons
        nav = []
        if page > 0:
            nav.append(("⬅ Prev", "prev"))
        if page < total - 1:
            nav.append(("Next ➡", "next"))

        kb = InlineKeyboardMarkup()

        for b in buttons:
            kb.add(InlineKeyboardButton(b[0], callback_data=b[1]))

        if nav:
            row = [InlineKeyboardButton(n[0], callback_data=n[1]) for n in nav]
            kb.row(*row)

        kb.add(InlineKeyboardButton("⬅ Back", callback_data="home"))

        text = f"📚 Page {page+1}/{total}"

        edit(chat_id, msg_id, text, kb)