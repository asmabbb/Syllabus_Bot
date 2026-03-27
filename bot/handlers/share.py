from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.config import ADMINS
from bot.keyboards.main_menu_keyboard import main_menu

# -------------------------
# STATE
# -------------------------
share_state = {}   # {chat_id: {"active": True, "message": message}}


def register_share_handlers(bot):

    # -------------------------
    # ENTER SHARE MODE
    # -------------------------
    @bot.message_handler(func=lambda m: m.text == "📤 Share Resources")
    def enter_share_mode(message):

        chat_id = message.chat.id

        share_state[chat_id] = {"active": True}

        bot.send_message(
            chat_id,
            "📤 *Share Mode Activated*\n\n"
            "Send your resource (file/photo/text).\n\n"
            "⚠️ You must confirm before sending.\n"
            "Send /cancel to exit.",
            parse_mode="Markdown"
        )


    # -------------------------
    # UNIVERSAL SHARE MODE ROUTER
    # (THIS FIXES EVERYTHING)
    # -------------------------
    @bot.message_handler(func=lambda m: m.chat.id in share_state and share_state[m.chat.id].get("active"), content_types=["text", "photo", "document", "video", "audio"])
    def share_router(message):

        chat_id = message.chat.id

        # -------- CANCEL COMMAND --------
        if message.text == "/cancel":
            share_state.pop(chat_id, None)

            bot.send_message(
                chat_id,
                "❌ Share mode exited.",
                reply_markup=main_menu(is_admin=(message.from_user.id in ADMINS))
            )
            return

        # -------- BLOCK MENU BUTTONS --------
        if message.text in ["📚 المناهج", "📤 Share Resources", "⚙️ Admin Panel"]:
            bot.send_message(
                chat_id,
                "⚠️ You're in share mode.\nSend a resource or type /cancel to exit."
            )
            return

        # -------- STORE MESSAGE --------
        share_state[chat_id]["message"] = message

        # -------- CONFIRM UI --------
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ Confirm", callback_data="share:confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="share:cancel")
        )

        bot.send_message(
            chat_id,
            "Do you want to send this resource to admins?",
            reply_markup=markup
        )


    # -------------------------
    # SINGLE CALLBACK ROUTER
    # -------------------------
    @bot.callback_query_handler(func=lambda c: c.data.startswith("share:"))
    def share_callback_router(call):

        chat_id = call.message.chat.id

        if chat_id not in share_state:
            bot.answer_callback_query(call.id, "Session expired.")
            return

        action = call.data.split(":")[1]

        # -------- CONFIRM --------
        if action == "confirm":

            state = share_state.get(chat_id)

            if not state or "message" not in state:
                bot.answer_callback_query(call.id, "No resource found.")
                return

            msg = state["message"]

            for admin_id in ADMINS:
                try:
                    bot.forward_message(
                        admin_id,
                        msg.chat.id,
                        msg.message_id
                    )
                except:
                    pass

            share_state.pop(chat_id, None)

            bot.answer_callback_query(call.id, "Sent!")

            bot.edit_message_text(
                "✅ Resource sent successfully!",
                chat_id,
                call.message.message_id
            )

            bot.send_message(
                chat_id,
                "Back to menu 👇",
                reply_markup=main_menu(is_admin=(call.from_user.id in ADMINS))
            )


        # -------- CANCEL --------
        elif action == "cancel":

            share_state.pop(chat_id, None)

            bot.answer_callback_query(call.id, "Cancelled.")

            bot.edit_message_text(
                "❌ Share cancelled.",
                chat_id,
                call.message.message_id
            )

            bot.send_message(
                chat_id,
                "Back to menu 👇",
                reply_markup=main_menu(is_admin=(call.from_user.id in ADMINS))
            )