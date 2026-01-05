# database.py dosyasının en altına ekleyin:

def get_student_grades(student_username):
    conn = connect()
    cursor = conn.cursor()
    # Sadece giriş yapan öğrencinin notlarını filtreliyoruz (WHERE student_username = ?)
    cursor.execute("SELECT lesson, grade, date FROM grades WHERE student_username = ?", (student_username,))
    grades = cursor.fetchall()
    conn.close()
    return grades
