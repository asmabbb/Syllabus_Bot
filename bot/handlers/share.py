from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.config import ADMINS
from bot.keyboards.main_menu_keyboard import main_menu

# -------------------------
# STATE
# -------------------------
share_state = {}  # {chat_id: {"step": "waiting_resource" / "waiting_confirm", "message": msg}}

MAIN_MENU_BUTTONS = ["📚 المناهج", "📤 Share Resources", "⚙️ Admin Panel"]


def register_share_handlers(bot):

    # -------------------------
    # ENTER SHARE MODE
    # -------------------------
    @bot.message_handler(func=lambda m: m.text == "📤 Share Resources")
    def enter_share_mode(message):
        chat_id = message.chat.id

        share_state[chat_id] = {
            "step": "waiting_resource",
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
    # 🔒 SHARE MODE ROUTER (ONLY HANDLER INSIDE MODE)
    # -------------------------
    @bot.message_handler(
        func=lambda m: m.chat.id in share_state,
        content_types=["text", "photo", "document", "video", "audio"]
    )
    def share_mode_router(message):

        chat_id = message.chat.id
        state = share_state.get(chat_id)

        if not state:
            return

        # -------- CANCEL COMMAND --------
        if message.text and message.text.strip() == "/cancel":
            share_state.pop(chat_id, None)

            bot.send_message(
                chat_id,
                "❌ Share mode exited.",
                reply_markup=main_menu(is_admin=(message.from_user.id in ADMINS))
            )
            return

        # -------- BLOCK MAIN MENU BUTTONS --------
        if message.text in MAIN_MENU_BUTTONS:
            bot.send_message(
                chat_id,
                "⚠️ You're in share mode.\nSend a resource or type /cancel to exit."
            )
            return

        # -------- STEP 1: WAITING RESOURCE --------
        if state["step"] == "waiting_resource":

            state["message"] = message
            state["step"] = "waiting_confirm"

            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("✅ Confirm", callback_data=f"share_confirm:{chat_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"share_cancel:{chat_id}")
            )

            bot.send_message(
                chat_id,
                "Do you want to send this resource to admins?",
                reply_markup=markup
            )
            return

        # -------- STEP 2: WAITING CONFIRM --------
        if state["step"] == "waiting_confirm":
            bot.send_message(
                chat_id,
                "⚠️ Please confirm or cancel the previous resource first."
            )
            return

    # -------------------------
    # CALLBACK HANDLER (STRICT)
    # -------------------------
    @bot.callback_query_handler(func=lambda c: c.data.startswith("share_"))
    def share_callback_handler(call):

        try:
            action, chat_id = call.data.split(":")
            chat_id = int(chat_id)
        except:
            bot.answer_callback_query(call.id, "Invalid action.")
            return

        state = share_state.get(chat_id)

        if not state:
            bot.answer_callback_query(call.id, "Session expired.")
            return

        # -------- CONFIRM --------
        if action == "share_confirm":

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
                call.message.chat.id,
                call.message.message_id
            )

            bot.send_message(
                chat_id,
                "Back to menu 👇",
                reply_markup=main_menu(is_admin=(call.from_user.id in ADMINS))
            )

        # -------- CANCEL --------
        elif action == "share_cancel":

            share_state.pop(chat_id, None)

            bot.answer_callback_query(call.id, "❌ Cancelled.")

            bot.edit_message_text(
                "❌ Share cancelled.",
                call.message.chat.id,
                call.message.message_id
            )

            bot.send_message(
                chat_id,
                "Back to menu 👇",
                reply_markup=main_menu(is_admin=(call.from_user.id in ADMINS))
            )