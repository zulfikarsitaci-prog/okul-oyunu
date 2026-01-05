# database.py
import sqlite3
import hashlib
from datetime import datetime

def connect():
    return sqlite3.connect('education_platform.db', check_same_thread=False)

def create_database():
    conn = connect()
    cursor = conn.cursor()
    
    # Kullanıcılar Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users
        (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT)
    ''')
    
    # Duyurular Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS announcements
        (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT, date TEXT, author TEXT)
    ''')
    
    # Notlar Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grades
        (id INTEGER PRIMARY KEY AUTOINCREMENT, student_username TEXT, lesson TEXT, grade INTEGER, date TEXT)
    ''')
    
    conn.commit()
    conn.close()

# --- KULLANICI İŞLEMLERİ ---
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
    cursor = conn.cursor()
    cursor.execute("SELECT username, role FROM users")
    users = cursor.fetchall()
    conn.close()
    return users

def delete_user(username):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def get_students():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE role = 'student'")
    students = [row[0] for row in cursor.fetchall()]
    conn.close()
    return students

# --- DUYURU İŞLEMLERİ ---
def add_announcement(title, content, author):
    conn = connect()
    cursor = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute("INSERT INTO announcements (title, content, date, author) VALUES (?, ?, ?, ?)", (title, content, date, author))
    conn.commit()
    conn.close()

def get_announcements():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM announcements ORDER BY id DESC")
    items = cursor.fetchall()
    conn.close()
    return items

# --- NOT İŞLEMLERİ ---
def add_grade(student_username, lesson, grade):
    conn = connect()
    cursor = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("INSERT INTO grades (student_username, lesson, grade, date) VALUES (?, ?, ?, ?)", (student_username, lesson, grade, date))
    conn.commit()
    conn.close()
