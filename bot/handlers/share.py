from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.config import ADMINS
from bot.keyboards.main_menu_keyboard import main_menu

# -------------------------
# STATE
# -------------------------
share_state = {}   # {chat_id: {"active": True, "message": message_object}}


# -------------------------
# REGISTER HANDLERS
# -------------------------
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
    # BLOCK MAIN MENU DURING SHARE MODE
    # -------------------------
    @bot.message_handler(func=lambda m: m.chat.id in share_state and share_state[m.chat.id].get("active") and m.text in [
        "📚 المناهج",
        "📤 Share Resources",
        "⚙️ Admin Panel"
    ])
    def block_menu_during_share(message):
        bot.send_message(
            message.chat.id,
            "⚠️ You're in share mode.\nSend a resource or type /cancel to exit."
        )


    # -------------------------
    # RECEIVE RESOURCE (ANY TYPE)
    # -------------------------
    @bot.message_handler(content_types=["text", "photo", "document", "video", "audio"])
    def receive_share(message):

        chat_id = message.chat.id

        if chat_id not in share_state or not share_state[chat_id].get("active"):
            return

        # Save message temporarily
        share_state[chat_id]["message"] = message

        # Confirmation keyboard
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ Confirm", callback_data="share_confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="share_cancel")
        )

        bot.send_message(
            chat_id,
            "Do you want to send this resource to admins?",
            reply_markup=markup
        )


    # -------------------------
    # CONFIRM SHARE
    # -------------------------
    @bot.callback_query_handler(func=lambda c: c.data == "share_confirm")
    def confirm_share(call):

        chat_id = call.message.chat.id

        state = share_state.get(chat_id)

        if not state or "message" not in state:
            bot.answer_callback_query(call.id, "No resource found.")
            return

        msg = state["message"]

        # Forward to all admins
        for admin_id in ADMINS:
            try:
                bot.forward_message(
                    admin_id,
                    msg.chat.id,
                    msg.message_id
                )
            except:
                pass  # ignore failures silently

        bot.answer_callback_query(call.id, "Resource sent!")

        # Exit share mode
        share_state.pop(chat_id, None)

        bot.send_message(
            chat_id,
            "✅ Resource sent successfully!",
            reply_markup=main_menu(is_admin=(call.from_user.id in ADMINS))
        )


    # -------------------------
    # CANCEL VIA BUTTON
    # -------------------------
    @bot.callback_query_handler(func=lambda c: c.data == "share_cancel")
    def cancel_share(call):

        chat_id = call.message.chat.id

        share_state.pop(chat_id, None)

        bot.answer_callback_query(call.id, "Cancelled.")

        bot.send_message(
            chat_id,
            "❌ Share cancelled.",
            reply_markup=main_menu(is_admin=(call.from_user.id in ADMINS))
        )


    # -------------------------
    # CANCEL VIA COMMAND
    # -------------------------
    @bot.message_handler(commands=["cancel"])
    def cancel_command(message):

        chat_id = message.chat.id

        if chat_id not in share_state:
            return

        share_state.pop(chat_id, None)

        bot.send_message(
            chat_id,
            "❌ Share mode exited.",
            reply_markup=main_menu(is_admin=(message.from_user.id in ADMINS))
        )