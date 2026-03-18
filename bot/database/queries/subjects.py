from bot.database.connection import get_connection


def get_subjects(semester_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name
        FROM subjects
        WHERE semester_id = %s
    """, (semester_id,))

    subjects = cur.fetchall()

    cur.close()
    conn.close()

    return subjects


def add_subject(semester_id, name):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO subjects (semester_id, name) VALUES (%s, %s)",
        (semester_id, name)
    )

    conn.commit()
    cur.close()
    conn.close()


def delete_subject(subject_id):

    conn = get_connection()
    cur = conn.cursor()

    # 1. Delete resources first
    cur.execute(
        "DELETE FROM resources WHERE subject_id = %s",
        (subject_id,)
    )

    # 2. Delete subject
    cur.execute(
        "DELETE FROM subjects WHERE id = %s",
        (subject_id,)
    )

    conn.commit()
    cur.close()
    conn.close()