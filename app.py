import streamlit as st
import database
import hashlib

# Veritabanı oluştur
database.create_database()

def create_admin_user():
    database.add_user("admin", "6626", "admin")

create_admin_user()

# Uygulama başlığı
st.title("Eğitim Platformu")

# Kullanıcı girişi formu
with st.form("login_form"):
    username = st.text_input("Kullanıcı Adı")
    password = st.text_input("Şifre", type="password")
    if st.form_submit_button("Giriş Yap"):
        # Şifreyi hash