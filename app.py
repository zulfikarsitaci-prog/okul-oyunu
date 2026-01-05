# App.py
import streamlit as st
import database
import time

# Sayfa ayarları
st.set_page_config(page_title="Eğitim Platformu", page_icon="🎓")

# 1. Veritabanını başlat
database.create_database()

# 2. Admin kullanıcısını oluştur (Sadece veritabanı boşsa veya admin yoksa çalışır)
# Database.py'deki UNIQUE kısıtlaması sayesinde hata vermeden geçer.
database.add_user("admin", "6626", "admin") 

# 3. Session State Tanımlamaları (Oturum durumunu hafızada tutmak için)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "username" not in st.session_state:
    st.session_state.username = None

# --- ARAYÜZ MANTIĞI ---

st.title("🎓 Eğitim Platformu")

# DURUM 1: KULLANICI GİRİŞ YAPMAMIŞSA
if not st.session_state.logged_in:
    st.subheader("Giriş Yap")
    
    with st.form("login_form"):
        username = st.text_input("Kullanıcı Adı")
        password = st.text_input("Şifre", type="password")
        submit_btn = st.form_submit_button("Giriş Yap")
        
        if submit_btn:
            user = database.login_user(username, password)
            if user:
                # Giriş başarılı, session bilgilerini güncelle
                st.session_state.logged_in = True
                st.session_state.user_role = user[3] # Role sütunu
                st.session_state.username = user[1]  # Username sütunu
                st.success("Giriş başarılı! Yönlendiriliyorsunuz...")
                time.sleep(1)
                st.rerun() # Sayfayı yenile ve paneli göster
            else:
                st.error("Hatalı kullanıcı adı veya şifre!")

# DURUM 2: KULLANICI GİRİŞ YAPMIŞSA
else:
    # Yan menü (Sidebar) oluştur
    with st.sidebar:
        st.write(f"👤 Aktif Kullanıcı: **{st.session_state.username}**")
        st.write(f"Rol: {st.session_state.user_role}")
        
        if st.button("Çıkış Yap"):
            st.session_state.logged_in = False
            st.session_state.user_role = None
            st.rerun()

    # Rol tabanlı içerik gösterimi
    if st.session_state.user_role == "admin":
        st.header("Admin Paneli")
        st.info("Sistem yönetimi ve kullanıcı işlemleri.")
        
        # --- KULLANICI EKLEME (Sadece Admin Görebilir) ---
        st.subheader("Yeni Kullanıcı Ekle")
        with st.form("add_user_form"):
            new_user = st.text_input("Yeni Kullanıcı Adı")
            new_pass = st.text_input("Yeni Şifre", type="password")
            new_role = st.selectbox("Rol Seçin", ["admin", "teacher", "student"])
            add_submitted = st.form_submit_button("Kullanıcıyı Kaydet")
            
            if add_submitted:
                if len(new_pass) < 4:
                    st.warning("Şifre en az 4 karakter olmalı.")
                else:
                    result = database.add_user(new_user, new_pass, new_role)
                    if result:
                        st.success(f"{new_user} kullanıcısı başarıyla oluşturuldu.")
                    else:
                        st.error("Bu kullanıcı adı zaten kullanılıyor!")

    elif st.session_state.user_role == "teacher":
        st.header("Öğretmen Paneli")
        st.write("Ders programları ve öğrenci notlarını buradan yönetebilirsiniz.")
        # Buraya öğretmen fonksiyonları gelecek

    elif st.session_state.user_role == "student":
        st.header("Öğrenci Paneli")
        st.write("Ders notlarınızı ve duyuruları buradan takip edebilirsiniz.")
        # Buraya öğrenci fonksiyonları gelecek
