import sqlite3
import hashlib

def create_database():
    conn = sqlite3.connect('education_platform.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_user(username, password, role):
    conn = sqlite3.connect('education_platform.db')
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed_password, role))
    conn.commit()
    conn.close()

def connect():
    return sqlite3.connect('education_platform.db')