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


    from bot.database.connection import get_connection

# ---------------------- GETTERS ----------------------
def get_semesters_by_major(major_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT number FROM semesters WHERE major_id = %s ORDER BY number",
        (major_id,)
    )
    semesters = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return semesters

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

# ---------------------- CRUD ----------------------
def add_semester(major_id, semester_number):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO semesters (major_id, number) VALUES (%s, %s) RETURNING id",
        (major_id, semester_number)
    )
    semester_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return semester_id

def delete_semester(semester_id):
    conn = get_connection()
    cur = conn.cursor()
    # Delete all subjects and their resources first
    cur.execute("SELECT id FROM subjects WHERE semester_id = %s", (semester_id,))
    subjects = [row[0] for row in cur.fetchall()]
    for sub_id in subjects:
        cur.execute("DELETE FROM resources WHERE subject_id = %s", (sub_id,))
    cur.execute("DELETE FROM subjects WHERE semester_id = %s", (semester_id,))
    # Delete the semester
    cur.execute("DELETE FROM semesters WHERE id = %s", (semester_id,))
    conn.commit()
    cur.close()
    conn.close()