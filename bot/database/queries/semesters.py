from bot.database.connection import get_connection


def get_semesters_by_major(major_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT number FROM semesters WHERE major_id = %s ORDER BY number",
        (major_id,)
    )

    semesters = cur.fetchall()

    cur.close()
    conn.close()

    return [sem[0] for sem in semesters]


def get_semester_id(major_id, semester_number):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id FROM semesters WHERE major_id = %s AND number = %s",
        (major_id, semester_number)
    )

    result = cur.fetchone()

    cur.close()
    conn.close()

    return result[0] if result else None