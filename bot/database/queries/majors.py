from bot.database.connection import get_connection


def get_majors():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, name FROM majors")
    majors = cur.fetchall()

    cur.close()
    conn.close()

    return majors


def add_major(name, start_semester, end_semester):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO majors (name, start_semester, end_semester) VALUES (%s, %s, %s) RETURNING id",
        (name, start_semester, end_semester)
    )

    major_id = cur.fetchone()[0]

    for i in range(start_semester, end_semester + 1):
        cur.execute(
            "INSERT INTO semesters (major_id, number) VALUES (%s, %s)",
            (major_id, i)
        )

    conn.commit()
    cur.close()
    conn.close()


def update_major(major_id, name):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE majors SET name = %s WHERE id = %s",
        (name, major_id)
    )

    conn.commit()
    cur.close()
    conn.close()


from bot.database.connection import get_connection

def delete_major(major_id):
    conn = get_connection()
    cur = conn.cursor()

    # 1. Delete resources (deepest level)
    cur.execute("""
        DELETE FROM resources
        WHERE subject_id IN (
            SELECT id FROM subjects
            WHERE semester_id IN (
                SELECT id FROM semesters WHERE major_id = %s
            )
        )
    """, (major_id,))

    # 2. Delete subjects
    cur.execute("""
        DELETE FROM subjects
        WHERE semester_id IN (
            SELECT id FROM semesters WHERE major_id = %s
        )
    """, (major_id,))

    # 3. Delete semesters
    cur.execute("""
        DELETE FROM semesters WHERE major_id = %s
    """, (major_id,))

    # 4. Delete the major
    cur.execute("""
        DELETE FROM majors WHERE id = %s
    """, (major_id,))

    conn.commit()
    cur.close()
    conn.close()