from bot.database.connection import get_connection


def add_resource(subject_id, category, title, file_id, year, season):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO resources
        (subject_id, category, title, file_id, academic_year, season)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (subject_id, category, title, file_id, year, season))

    conn.commit()
    cur.close()
    conn.close()


def get_resources(subject_id, category):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT title, file_id, academic_year, season
        FROM resources
        WHERE subject_id=%s AND category=%s
        ORDER BY 
            academic_year DESC,
            CASE 
                WHEN season = 'fall' THEN 3
                WHEN season = 'summer' THEN 2
                WHEN season = 'spring' THEN 1
                ELSE 0
            END DESC
    """, (subject_id, category))

    data = cur.fetchall()

    cur.close()
    conn.close()

    return data


def get_all_resources():
    """Debug function to get all resources"""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT r.title, r.category, s.name as subject_name, m.name as major_name
        FROM resources r
        JOIN subjects s ON r.subject_id = s.id
        JOIN semesters sem ON s.semester_id = sem.id
        JOIN majors m ON sem.major_id = m.id
    """)

    data = cur.fetchall()

    cur.close()
    conn.close()

    return data


def get_categories_for_subject(subject_id):
    """Debug function to get categories for a subject"""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT category
        FROM resources
        WHERE subject_id = %s
    """, (subject_id,))

    data = cur.fetchall()

    cur.close()
    conn.close()

    return data


def delete_resource(resource_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM resources WHERE id = %s",
        (resource_id,)
    )

    conn.commit()
    cur.close()
    conn.close()


def update_resource(resource_id, title=None, category=None, year=None, season=None):
    """Update resource details"""
    conn = get_connection()
    cur = conn.cursor()
    
    fields = []
    values = []
    if title is not None:
        fields.append("title=%s")
        values.append(title)
    if category is not None:
        fields.append("category=%s")
        values.append(category)
    if year is not None:
        fields.append("academic_year=%s")
        values.append(year)
    if season is not None:
        fields.append("season=%s")
        values.append(season)
    
    if not fields:
        cur.close()
        conn.close()
        return
    
    query = f"UPDATE resources SET {', '.join(fields)} WHERE id=%s"
    values.append(resource_id)
    
    cur.execute(query, tuple(values))
    conn.commit()
    cur.close()
    conn.close()