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

    # 1. Get all semester IDs
    cur.execute("SELECT id FROM semesters WHERE major_id = %s", (major_id,))
    semesters = [row[0] for row in cur.fetchall()]

    if semesters:
        # 2. Get all subject IDs
        cur.execute(
            "SELECT id FROM subjects WHERE semester_id = ANY(%s)",
            (semesters,)
        )
        subjects = [row[0] for row in cur.fetchall()]

        if subjects:
            # 3. Delete resources
            cur.execute(
                "DELETE FROM resources WHERE subject_id = ANY(%s)",
                (subjects,)
            )

            # 4. Delete subjects
            cur.execute(
                "DELETE FROM subjects WHERE id = ANY(%s)",
                (subjects,)
            )

        # 5. Delete semesters
        cur.execute(
            "DELETE FROM semesters WHERE id = ANY(%s)",
            (semesters,)
        )

    # 6. Delete major
    cur.execute("DELETE FROM majors WHERE id = %s", (major_id,))

    conn.commit()
    cur.close()
    conn.close()