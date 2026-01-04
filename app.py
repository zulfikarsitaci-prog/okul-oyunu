import streamlit as st
import database
import hashlib

# Veritabanı oluştur
database.create_database()

def create_admin_user():
    database.add_user("admin", "password123", "admin")

create_admin_user()

# Uygulama başlığı
st.title("Eğitim Platformu")

# Kullanıcı girişi formu
with st.form("login_form"):
    username = st.text_input("Kullanıcı Adı")
    password = st.text_input("Şifre", type="password")
    if st.form_submit_button("Giriş Yap"):
        # Şifreyi hashle
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        # Veritabanında kullanıcı ara
        conn = database.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password))
        user = cursor.fetchone()
        if user:
            st.session_state.logged_in = True
            st.session_state.user_role = user[3]
            st.rerun()
        else:
            st.error("Hatalı kullanıcı adı veya şifre")
        conn.close()

# Kullanıcı girişi başarılıysa
if st.session_state.get("logged_in", False):
    # Kullanıcı rolüne göre işlem yap
    if st.session_state.user_role == "admin":
        st.write("Admin paneli")
    elif st.session_state.user_role == "teacher":
        st.write("Öğretmen paneli")
    elif st.session_state.user_role == "student":
        st.write("Öğrenci paneli")

# Kullanıcı ekleme formu
with st.form("add_user_form"):
    username = st.text_input("Kullanıcı Adı", key="add_username")
    password = st.text_input("Şifre", type="password", key="add_password")
    role = st.selectbox("Rol", ["admin", "teacher", "student"], key="add_role")