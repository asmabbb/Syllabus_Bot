from bot.database.connection import get_connection


def get_majors():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, name FROM majors")
    majors = cur.fetchall()

    cur.close()
    conn.close()

    return majors


def add_major(name):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO majors (name) VALUES (%s)",
        (name,)
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


def delete_major(major_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM majors WHERE id = %s",
        (major_id,)
    )

    conn.commit()
    cur.close()
    conn.close()