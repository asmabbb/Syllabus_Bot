from bot.database.connection import get_connection

def get_admins():
    """Return a list of all admin user_ids"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE role='admin'")
    admins = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return admins

def add_admin(user_id):
    """Promote a user to admin"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET role='admin' WHERE user_id=%s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

def delete_admin(user_id):
    """Demote admin to student"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET role='student' WHERE user_id=%s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()