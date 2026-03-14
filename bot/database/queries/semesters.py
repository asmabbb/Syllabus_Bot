from bot.database.connection import get_connection


def get_semester_id(major_id, semester_number):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id FROM semesters WHERE major_id = %s AND semester_number = %s",
        (major_id, semester_number)
    )

    result = cur.fetchone()

    cur.close()
    conn.close()

    return result[0] if result else None