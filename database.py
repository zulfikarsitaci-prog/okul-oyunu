# Database.py
import sqlite3
import hashlib

def connect():
    # check_same_thread=False streamlit için gereklidir
    return sqlite3.connect('education_platform.db', check_same_thread=False)

def create_database():
    conn = connect()
    cursor = conn.cursor()
    # Username alanına UNIQUE ekledik, aynı isimde iki kullanıcı olamaz.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users
        (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT)
    ''')
    conn.commit()
    conn.close()

def add_user(username, password, role):
    conn = connect()
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    try:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed_password, role))
        conn.commit()
        return True # Başarılı
    except sqlite3.IntegrityError:
        # Bu kullanıcı adı zaten varsa hata vermez, sadece eklemez.
        return False 
    except sqlite3.Error as e:
        print(f"Hata: {e}")
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
