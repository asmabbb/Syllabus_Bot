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