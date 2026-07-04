from bot.database.connection import get_connection

def get_role(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """ Select role
            FROM users
            where user_id = %s
            """, 
            (user_id,)
    )

    result = cur.fetchone()

    cur.close()
    conn.close()

    if result:
        return result[0]
    
    return "student"


def get_minor_admins():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT user_id
        FROM users
        WHERE role = 'minor_admin'
        order by user_id
    """
    )

    admins = [row[0] for row in cur.fetchall()]

    cur.close()
    conn.close()

    return admins


def get_super_admins():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT user_id
        FROM users
        WHERE role = 'super_admin'
        order by user_id
    """
    )

    admins = [row[0] for row in cur.fetchall()]

    cur.close()
    conn.close()

    return admins



def get_all_admins():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT user_id
        FROM users
        where role IN ('super_admin', 'minor_admin')
        order by role DESC, user_id
"""
    )

    admins = cur.fetchall()

    cur.close()
    conn.close()

    return admins


def make_minor_admin(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        update users
        set role = 'minor_admin'
        where user_id = %s""",
        (user_id,)
    )

    conn.commit()

    cur.close()
    conn.close()


def make_super_admin(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        update users 
        set role = 'super_admin'
        where user_id = %s""",
        (user_id,)
    )

    conn.commit()

    cur.close()
    conn.close()


def remove_admin(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        update users
        set role = 'student'
        where user_id = %s""",
        (user_id,)

    )

    conn.commit()
    
    cur.close()
    conn.close()


