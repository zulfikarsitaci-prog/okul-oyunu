import sqlite3
import hashlib
import os
import streamlit as st
from datetime import datetime
import base64
from PIL import Image
import io

# --- BAĞLANTI ---
@st.cache_resource(ttl=3600)
def get_db_connection():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "education_platform_pro.db")
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def run_query(query, params=(), fetch=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if fetch: return cursor.fetchall()
        else: conn.commit(); return True
    except Exception as e: return False
    finally: cursor.close()

def create_database():
    tables = [
        'CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT, score INTEGER DEFAULT 5000, bio TEXT, avatar_data TEXT, frame TEXT, name_style TEXT, class_code TEXT)',
        'CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, content TEXT, image_data TEXT, youtube_link TEXT, wall_type TEXT, target_class TEXT, timestamp TEXT, likes INTEGER DEFAULT 0)',
        'CREATE TABLE IF NOT EXISTS comments (id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER, username TEXT, content TEXT, timestamp TEXT, is_read INTEGER DEFAULT 0)',
        'CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT, receiver TEXT, message TEXT, timestamp TEXT, is_read INTEGER DEFAULT 0)',
        'CREATE TABLE IF NOT EXISTS followers (id INTEGER PRIMARY KEY AUTOINCREMENT, follower TEXT, followed TEXT)',
        'CREATE TABLE IF NOT EXISTS classes (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE, name TEXT, teacher TEXT)',
        'CREATE TABLE IF NOT EXISTS grades (id INTEGER PRIMARY KEY AUTOINCREMENT, student_username TEXT, lesson TEXT, grade INTEGER, date TEXT)'
    ]
    for t in tables: run_query(t)
    
    if not login_user("admin", "6626"):
        h = hashlib.sha256("6626".encode()).hexdigest()
        run_query("INSERT INTO users (username, password, role, score, bio) VALUES (?, ?, ?, ?, ?)", ("admin", h, "admin", 9999999, "Sistem Yöneticisi"))

# --- KULLANICI ---
def login_user(u, p):
    h = hashlib.sha256(p.encode()).hexdigest()
    res = run_query("SELECT id, username, password, role, score, bio, avatar_data, frame, name_style, class_code FROM users WHERE username = ? AND password = ?", (u, h), fetch=True)
    return res[0] if res else None

def add_user(u, p, r):
    try:
        h = hashlib.sha256(p.encode()).hexdigest()
        run_query("INSERT INTO users (username, password, role, score, bio) VALUES (?, ?, ?, ?, ?)", (u, h, r, 5000, "Yeni Öğrenci"))
        return True, 0
    except: return False, 0

def get_user_data(u):
    res = run_query("SELECT score, bio, avatar_data, frame, name_style, role, class_code FROM users WHERE username = ?", (u,), fetch=True)
    return res[0] if res else (0, "", None, None, None, "student", None)

def update_bio(u, bio): run_query("UPDATE users SET bio = ? WHERE username = ?", (bio, u))

def update_avatar(u, img_file):
    try:
        img = Image.open(img_file).convert("RGB"); img.thumbnail((400, 400)); buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=60)
        img_str = base64.b64encode(buffer.getvalue()).decode()
        run_query("UPDATE users SET avatar_data = ? WHERE username = ?", (img_str, u))
        return True
    except: return False

def get_user_change_count(u): return 0 
def change_username_logic(old_u, new_u):
    try:
        run_query("UPDATE users SET username = ? WHERE username = ?", (new_u, old_u))
        for t in ["posts", "comments", "grades"]: run_query(f"UPDATE {t} SET username = ? WHERE username = ?", (new_u, old_u))
        return True, "Değişti"
    except: return False, "Kullanımda"

# --- SOSYAL ---
def follow_user(follower, followed):
    if follower == followed: return False
    if not run_query("SELECT id FROM followers WHERE follower = ? AND followed = ?", (follower, followed), fetch=True):
        run_query("INSERT INTO followers (follower, followed) VALUES (?, ?)", (follower, followed))
        # Takip bildirim
        send_message("Sistem", followed, f"{follower} seni takip etmeye başladı!")
        return True
    return False

def get_followers_count(u): return run_query("SELECT COUNT(*) FROM followers WHERE followed = ?", (u,), fetch=True)[0][0]
def get_following_count(u): return run_query("SELECT COUNT(*) FROM followers WHERE follower = ?", (u,), fetch=True)[0][0]
def get_mutual_friends(u):
    return [r[0] for r in run_query("SELECT f1.followed FROM followers f1 JOIN followers f2 ON f1.followed = f2.follower WHERE f1.follower = ? AND f2.followed = ?", (u, u), fetch=True)]
def get_all_users_list(exclude_me=None):
    q = "SELECT username FROM users WHERE username != 'admin'" + (" AND username != ?" if exclude_me else "")
    p = (exclude_me,) if exclude_me else ()
    return [r[0] for r in run_query(q, p, fetch=True)]
def get_searchable_users(u): return get_all_users_list(u)
def get_pending_requests(u): return [] 
def accept_request(s, r): pass

# --- İÇERİK ---
def add_post(u, c, img=None, yt=None, w_type="campus", t_class=None):
    img_d = None
    if img:
        try: im = Image.open(img).convert("RGB"); im.thumbnail((600,600)); buf = io.BytesIO(); im.save(buf, format="JPEG"); img_d = base64.b64encode(buf.getvalue()).decode()
        except: pass
    t = datetime.now().strftime("%Y-%m-%d %H:%M")
    run_query("INSERT INTO posts (username, content, image_data, youtube_link, wall_type, target_class, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)", (u, c, img_d, yt, w_type, t_class, t))

def get_posts(limit=50, wall_type="campus", target_class=None, user_filter=None):
    if user_filter: 
        return run_query("SELECT id, username, content, image_data, youtube_link, timestamp, likes FROM posts WHERE username = ? ORDER BY id DESC LIMIT ?", (user_filter, limit), fetch=True)
    elif wall_type == "class":
        return run_query("SELECT id, username, content, image_data, youtube_link, timestamp, likes FROM posts WHERE wall_type = 'class' AND target_class = ? ORDER BY id DESC LIMIT ?", (target_class, limit), fetch=True)
    else: # Campus
        return run_query("SELECT id, username, content, image_data, youtube_link, timestamp, likes FROM posts WHERE wall_type = 'campus' ORDER BY id DESC LIMIT ?", (limit,), fetch=True)

def like_post(id): run_query("UPDATE posts SET likes = likes + 1 WHERE id = ?", (id,))
def delete_post(pid): run_query("DELETE FROM posts WHERE id=?",(pid,)); run_query("DELETE FROM comments WHERE post_id=?",(pid,))
def add_comment(pid, u, c): 
    run_query("INSERT INTO comments (post_id, username, content, timestamp) VALUES (?, ?, ?, ?)", (pid, u, c, datetime.now().strftime("%Y-%m-%d %H:%M")))
def get_comments(pid): return run_query("SELECT username, content FROM comments WHERE post_id = ?", (pid,), fetch=True) or []

# --- PUAN & MAĞAZA ---
def add_score(u, val, reason="Sistem"): run_query("UPDATE users SET score = score + ? WHERE username = ?", (val, u))
def buy_item(u, item_type, item_val, cost):
    curr = get_user_data(u)[0]
    if curr >= cost:
        add_score(u, -cost)
        col = "frame" if item_type == "frame" else "name_style"
        run_query(f"UPDATE users SET {col} = ? WHERE username = ?", (item_val, u))
        return True, "Alındı"
    return False, "Yetersiz Bakiye"
def send_gift(s, r, item, cost):
    if get_user_data(s)[0] >= cost:
        add_score(s, -cost)
        send_message("Sistem", r, f"🎁 {s} sana bir hediye gönderdi: {item}!")
        return True, "Gönderildi"
    return False, "Yetersiz Bakiye"

# --- MESAJLAŞMA & BİLDİRİM ---
def send_message(s, r, m): run_query("INSERT INTO messages (sender, receiver, message, timestamp) VALUES (?, ?, ?, ?)", (s, r, m, datetime.now().strftime("%Y-%m-%d %H:%M")))
def get_conversation(u1, u2): return run_query("SELECT sender, message, timestamp FROM messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) ORDER BY id ASC", (u1, u2, u2, u1), fetch=True) or []
def get_unread_notification_count(u): return run_query("SELECT COUNT(*) FROM messages WHERE receiver = ? AND is_read = 0", (u,), fetch=True)[0][0]
def get_unread_notifications(u):
    # Hem mesajları hem okunmamış yorumları çekebilirdik ama burada sadece mesajları bildirim olarak dönelim
    return run_query("SELECT sender, message, timestamp FROM messages WHERE receiver = ? AND is_read = 0", (u,), fetch=True) or []
def mark_notifications_read(u): run_query("UPDATE messages SET is_read = 1 WHERE receiver = ?", (u,))

# --- DİĞER ---
def create_class(t, n, c): 
    try: run_query("INSERT INTO classes (code, name, teacher) VALUES (?, ?, ?)", (c, n, t)); return True
    except: return False
def join_class(u, c):
    res = run_query("SELECT name FROM classes WHERE code = ?", (c,), fetch=True)
    if res: run_query("UPDATE users SET class_code = ? WHERE username = ?", (c, u)); return True, res[0][0]
    return False, None
def get_leaderboard_data(): return run_query("SELECT username, score FROM users WHERE role != 'admin' ORDER BY score DESC LIMIT 50", fetch=True) or []
def get_all_users(): return run_query("SELECT username, score, role, class_code FROM users", fetch=True)
def delete_user(u):
    run_query("DELETE FROM users WHERE username=?",(u,))
    run_query("DELETE FROM posts WHERE username=?",(u,))
    run_query("DELETE FROM comments WHERE username=?",(u,))
    run_query("DELETE FROM messages WHERE sender=? OR receiver=?",(u,u))
def admin_get_all_messages(): return run_query("SELECT sender, receiver, message, timestamp FROM messages ORDER BY id DESC LIMIT 100", fetch=True)
def update_activity(u): pass 
def get_user_styles(u):
    res = run_query("SELECT avatar_data, frame, name_style FROM users WHERE username = ?", (u,), fetch=True)
    return res[0] if res else (None, None, None)
def get_total_score(u): return get_user_data(u)[0]
def get_friends(u): return get_mutual_friends(u)
def get_user_role(u): return True
