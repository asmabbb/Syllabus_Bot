from bot.database.connection import get_connection

def get_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE user_id = %s",
        (user_id,)
    )
    user = cursor.fetchone()

    cursor.close()
    conn.close()
    return user


def create_user(user_id, role):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO users (user_id, role) VALUES (%s, %s)",
        (user_id, role)
    )

    conn.commit()
    cursor.close()
    conn.close()




def user_exists(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        select 1
        from users
        where user_id = %s
        """, (user_id,)
    )

    exits = cur.fetchone() is not None

    cur.close()
    conn.close()

    return exits