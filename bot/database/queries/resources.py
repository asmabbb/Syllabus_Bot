from bot.database.connection import get_connection


def add_resource(subject_id, category, title, file_id, year, season):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO resources
        (subject_id, category, title, file_id, academic_year, season)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (subject_id, category, title, file_id, year, season))

    conn.commit()
    cur.close()
    conn.close()


def get_resources(subject_id, category):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT title, file_id
        FROM resources
        WHERE subject_id=%s AND category=%s
        ORDER BY academic_year DESC
    """, (subject_id, category))

    data = cur.fetchall()

    cur.close()
    conn.close()

    return data