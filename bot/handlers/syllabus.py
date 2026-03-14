from telebot.types import ReplyKeyboardMarkup
from bot.database.queries.majors import get_majors
from bot.database.queries.subjects import get_subjects
from bot.database.queries.resources import get_resources

user_state = {}


def register_syllabus(bot):

    @bot.message_handler(func=lambda m: m.text == "📚 Syllabus")
    def syllabus_menu(message):

        majors = get_majors()

        markup = ReplyKeyboardMarkup(resize_keyboard=True)

        for major in majors:
            markup.add(major[1])

        bot.send_message(
            message.chat.id,
            "Choose Major:",
            reply_markup=markup
        )


    @bot.message_handler(func=lambda m: True)
    def major_selected(message):

        majors = get_majors()

        for major in majors:
            if message.text == major[1]:

                user_state[message.chat.id] = {"major_id": major[0]}

                subjects = get_subjects(major[0])

                markup = ReplyKeyboardMarkup(resize_keyboard=True)

                for subject in subjects:
                    markup.add(subject[1])

                bot.send_message(
                    message.chat.id,
                    "Choose Subject:",
                    reply_markup=markup
                )
                return

        # Check if it's a subject selection
        if message.chat.id in user_state and "major_id" in user_state[message.chat.id]:
            subjects = get_subjects(user_state[message.chat.id]["major_id"])
            for subject in subjects:
                if message.text == subject[1]:
                    user_state[message.chat.id]["subject_id"] = subject[0]
                    
                    # Show resource categories
                    markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    markup.add("Exams", "Lectures & Books", "Other resources")  # Add more categories as needed
                    
                    bot.send_message(
                        message.chat.id,
                        "Choose Resource Type:",
                        reply_markup=markup
                    )
                    return

        # Check if it's a category selection
        if message.chat.id in user_state and "subject_id" in user_state[message.chat.id]:
            subject_id = user_state[message.chat.id]["subject_id"]
            chat_id = message.chat.id
            
            if message.text == "Exams":
                resources = get_resources(subject_id, "exam")
                
                for title, file_id in resources:
                    bot.send_document(
                        chat_id,
                        file_id,
                        caption=title
                    )
                # Clear state or go back
                user_state.pop(message.chat.id, None)
                return
            # Add similar for other categories