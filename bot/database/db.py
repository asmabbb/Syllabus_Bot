from bot.database.connection import get_connection

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        user_id BIGINT UNIQUE,
        role TEXT DEFAULT 'student',
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS majors (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        start_semester INTEGER DEFAULT 1,
        end_semester INTEGER DEFAULT 8
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS semesters (
        id SERIAL PRIMARY KEY,
        major_id INTEGER REFERENCES majors(id) ON DELETE CASCADE,
        number INTEGER
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subjects (
        id SERIAL PRIMARY KEY,
        semester_id INTEGER REFERENCES semesters(id) ON DELETE CASCADE,
        name TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resources (
        id SERIAL PRIMARY KEY,
        subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
        category TEXT,
        title TEXT,
        file_id TEXT,
        academic_year INTEGER,
        season TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id SERIAL PRIMARY KEY,
        subject_id INTEGER REFERENCES subjects(id),
        question_text TEXT,
        option_a TEXT,
        option_b TEXT,
        option_c TEXT,
        option_d TEXT,
        correct_answer CHAR(1)
    );
    """)

    conn.commit()
    cursor.close()
    conn.close()