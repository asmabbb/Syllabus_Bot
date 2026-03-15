from bot.database.connection import get_connection


def get_subjects(major_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT subjects.id, subjects.name
        FROM subjects
        JOIN semesters ON subjects.semester_id = semesters.id
        WHERE semesters.major_id = %s
    """, (major_id,))

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

    cur.execute(
        "DELETE FROM subjects WHERE id = %s",
        (subject_id,)
    )

    conn.commit()
    cur.close()
    conn.close()