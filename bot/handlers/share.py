from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.config import ADMINS
from bot.keyboards.main_menu_keyboard import main_menu

share_state = {}
MAIN_MENU_BUTTONS = ["📚 المناهج", "📤 Share Resources", "⚙️ Admin Panel"]


def register_share_handlers(bot):

    # -------------------------
    # ENTER SHARE MODE
    # -------------------------
    @bot.message_handler(func=lambda m: m.text == "📤 Share Resources")
    def enter_share_mode(message):
        chat_id = message.chat.id

        share_state[chat_id] = {
            "active": True,
            "waiting_confirm": False,
            "message": None
        }

        bot.send_message(
            chat_id,
            "📤 *Share Mode Activated*\n\n"
            "Send your resource (file / photo / video / link / text).\n\n"
            "⚠️ You must confirm before sending.\n"
            "Send /cancel to exit.",
            parse_mode="Markdown"
        )


    # -------------------------
    # 🔥 HARD LOCK SHARE MODE
    # -------------------------
    @bot.message_handler(
        func=lambda m: m.chat.id in share_state,
        content_types=["text", "photo", "document", "video", "audio"]
    )
    def share_router(message):

        chat_id = message.chat.id
        state = share_state.get(chat_id)

        if not state or not state.get("active"):
            return

        # -------- FORCE STOP OTHER HANDLERS --------
        # (THIS IS THE MAGIC LINE)
        bot.stop_polling()  # temporarily stop
        bot.infinity_polling(skip_pending=True)  # restart clean

        # -------- CANCEL COMMAND --------
        if message.text and message.text.strip() == "/cancel":
            share_state.pop(chat_id, None)

            bot.send_message(
                chat_id,
                "❌ Share mode exited.",
                reply_markup=main_menu(is_admin=(message.from_user.id in ADMINS))
            )
            return

        # -------- BLOCK MENU --------
        if message.text in MAIN_MENU_BUTTONS:
            bot.send_message(
                chat_id,
                "⚠️ You're in share mode.\nSend a resource or type /cancel to exit."
            )
            return

        # -------- WAITING CONFIRM --------
        if state["waiting_confirm"]:
            bot.send_message(
                chat_id,
                "⚠️ Confirm or cancel your previous submission first."
            )
            return

        # -------- ACCEPT ANY CONTENT (INCLUDING LINKS) --------
        state["message"] = message
        state["waiting_confirm"] = True

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ Confirm", callback_data=f"share_confirm_{message.chat.from_user.id}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"share_cancel_{message.chat.from_user.id}")
        )

        bot.send_message(
            chat_id,
            "Do you want to send this resource to admins?",
            reply_markup=markup
        )


    # -------------------------
    # CALLBACK (STRICT)
    # -------------------------
    @bot.callback_query_handler(func=lambda c: c.data.startswith("share_confirm_") or c.data.startswith("share_cancel_"))
    def handle_share_callback(call):

        chat_id = call.message.chat.id
        state = share_state.get(chat_id)

        if not state:
            bot.answer_callback_query(call.id, "Session expired.")
            return

        # -------- CONFIRM --------
        if call.data.startswith("share_confirm_"):

            msg = state.get("message")

            if not msg:
                bot.answer_callback_query(call.id, "No resource found.")
                return

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

            bot.answer_callback_query(call.id, "✅ Sent!")

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
        elif call.data.startswith("share_cancel_"):

            share_state.pop(chat_id, None)

            bot.answer_callback_query(call.id, "❌ Cancelled.")

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