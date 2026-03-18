from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

ITEMS_PER_PAGE = 5


def paginate(items, page):
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    return items[start:end]


def pagination_keyboard(prefix, page, total_items):
    markup = InlineKeyboardMarkup()

    if page > 0:
        markup.add(
            InlineKeyboardButton("⬅ Prev", callback_data=f"{prefix}:page:{page-1}")
        )

    if (page + 1) * ITEMS_PER_PAGE < total_items:
        markup.add(
            InlineKeyboardButton("Next ➡", callback_data=f"{prefix}:page:{page+1}")
        )

    return markup
