from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from bot.config import ADMINS
from bot.keyboards.main_menu_keyboard import main_menu

# -------------------------
# STATE
# -------------------------
share_state = {}  # {chat_id: {"step": "...", "message": msg}}

MAIN_MENU_BUTTONS = ["📚 المناهج", "📤 Share Resources", "⚙️ Admin Panel"]


def confirm_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("✅ Confirm", "❌ Cancel")
    return markup


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
            "📤 Share Mode Activated\n\n"
            "Send your resource (file / photo / video / link / text).\n\n"
            "Then confirm or /cancel.",
        )


    # -------------------------
    # 🔒 HARD SHARE MODE ROUTER
    # -------------------------
    @bot.message_handler(
        func=lambda m: m.chat.id in share_state,
        content_types=["text", "photo", "document", "video", "audio"]
    )
    def share_router(message):

        chat_id = message.chat.id
        state = share_state.get(chat_id)

        if not state:
            return

        # -------- FORCE BLOCK EVERYTHING ELSE --------
        # (THIS makes share mode dominant)
        
        # -------- CANCEL COMMAND --------
        if message.text and message.text.strip().lower() == "/cancel":
            share_state.pop(chat_id, None)

            bot.send_message(
                chat_id,
                "❌ Share mode exited.",
                reply_markup=main_menu(is_admin=(message.from_user.id in ADMINS))
            )
            return

        # -------- BLOCK MAIN MENU --------
        if message.text in MAIN_MENU_BUTTONS:
            bot.send_message(
                chat_id,
                "⚠️ You're in share mode.\nSend a resource or type /cancel to exit."
            )
            return

        # -------------------------
        # STEP 1: RECEIVE RESOURCE
        # -------------------------
        if state["step"] == "waiting_resource":

            state["message"] = message
            state["step"] = "waiting_confirm"

            bot.send_message(
                chat_id,
                "Confirm sending this resource?",
                reply_markup=confirm_keyboard()
            )
            return

        # -------------------------
        # STEP 2: CONFIRM / CANCEL
        # -------------------------
        if state["step"] == "waiting_confirm":

            # CONFIRM
            if message.text == "✅ Confirm":

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

                bot.send_message(
                    chat_id,
                    "✅ Resource sent successfully!",
                    reply_markup=main_menu(is_admin=(message.from_user.id in ADMINS))
                )
                return

            # CANCEL
            if message.text == "❌ Cancel":
                share_state.pop(chat_id, None)

                bot.send_message(
                    chat_id,
                    "❌ Share cancelled.",
                    reply_markup=main_menu(is_admin=(message.from_user.id in ADMINS))
                )
                return

            # INVALID INPUT
            bot.send_message(
                chat_id,
                "⚠️ Please press Confirm or Cancel."
            )
            return