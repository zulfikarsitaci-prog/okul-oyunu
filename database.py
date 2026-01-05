def add_lesson(lesson_name, lesson_time, lesson_day):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO lessons (name, time, day) VALUES (?, ?, ?)", (lesson_name, lesson_time, lesson_day))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Hata: {e}")
    finally:
        conn.close()

def get_lessons():
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM lessons")
        lessons = cursor.fetchall()
        return lessons
    except sqlite3.Error as e:
        print(f"Hata: {e}")
    finally:
        conn.close()

def add_grade(student_name, lesson_name, grade):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO grades (student_name, lesson_name, grade) VALUES (?, ?, ?)", (student_name, lesson_name, grade))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Hata: {e}")
    finally:
        conn.close()

def get_grades():
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM grades")
        grades = cursor.fetchall()
        return grades
    except sqlite3.Error as e:
        print(f"Hata: {e}")
    finally:
        conn.close()

def get_users():
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        return users
    except sqlite3.Error as e:
        print(f"Hata: {e}")
    finally:
        conn.close()