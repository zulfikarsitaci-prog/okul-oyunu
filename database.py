import sqlite3
import hashlib
from datetime import datetime

def connect():
    return sqlite3.connect('education_platform.db', check_same_thread=False)

def create_database():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS announcements (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT, date TEXT, author TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS grades (id INTEGER PRIMARY KEY AUTOINCREMENT, student_username TEXT, lesson TEXT, grade INTEGER, date TEXT)''')
    conn.commit()
    conn.close()

def add_user(username, password, role):
    conn = connect()
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    try:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed_password, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_user(username, password):
    conn = connect()
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password))
    user = cursor.fetchone()
    conn.close()
    return user

def get_all_users():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT username, role FROM users")
    return c.fetchall()

def delete_user(username):
    conn = connect()
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def get_students():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE role = 'student'")
    return [row[0] for row in c.fetchall()]

def add_announcement(title, content, author):
    conn = connect()
    c = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT INTO announcements (title, content, date, author) VALUES (?, ?, ?, ?)", (title, content, date, author))
    conn.commit()
    conn.close()

def get_announcements():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM announcements ORDER BY id DESC")
    return c.fetchall()

def add_grade(student_username, lesson, grade):
    conn = connect()
    c = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d")
    c.execute("INSERT INTO grades (student_username, lesson, grade, date) VALUES (?, ?, ?, ?)", (student_username, lesson, grade, date))
    conn.commit()
    conn.close()

def get_student_grades(student_username):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT lesson, grade, date FROM grades WHERE student_username = ?", (student_username,))
    return c.fetchall()
