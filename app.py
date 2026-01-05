# App.py
import streamlit as st
import database
import time
import pandas as pd # Veriyi tablo olarak göstermek için

st.set_page_config(page_title="Eğitim Platformu", page_icon="🎓", layout="wide")

# Veritabanını başlat
database.create_database()
database.add_user("admin", "6626", "admin") 

# Session State Kontrolü
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None

# --- GİRİŞ EKRANI ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🎓 Okul Yönetim Sistemi</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("Kullanıcı Adı")
            password = st.text_input("Şifre", type="password")
            submit_btn = st.form_submit_button("Giriş Yap", use_container_width=True)
            
            if submit_btn:
                user = database.login_user(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_role = user[3]
                    st.session_state.username = user[1]
                    st.success("Giriş yapıldı!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Hatalı bilgiler.")

# --- PANEL EKRANLARI ---
else:
    # Sidebar (Yan Menü)
    with st.sidebar:
        st.write(f"Hoşgeldiniz, **{st.session_state.username}**")
        st.info(f"Yetki: {st.session_state.user_role.upper()}")
        if st.button("Çıkış Yap", type="primary"):
            st.session_state.logged_in = False
            st.rerun()

    # ---------------- ADMIN PANELİ ----------------
    if st.session_state.user_role == "admin":
        st.header("🛠️ Admin Yönetim Paneli")
        
        tab1, tab2 = st.tabs(["Kullanıcı Ekle", "Kullanıcı Listesi & Silme"])
        
        # Tab 1: Kullanıcı Ekleme
        with tab1:
            st.subheader("Yeni Kullanıcı Kaydı")
            col_a, col_b = st.columns(2)
            with col_a:
                new_user = st.text_input("Kullanıcı Adı")
                new_pass = st.text_input("Şifre", type="password")
            with col_b:
                new_role = st.selectbox("Rol", ["admin", "teacher", "student"])
                st.write("") # Boşluk
                st.write("") # Boşluk
                if st.button("Kullanıcıyı Kaydet"):
                    if len(new_pass) < 4:
                        st.warning("Şifre çok kısa!")
                    else:
                        if database.add_user(new_user, new_pass, new_role):
                            st.success(f"{new_user} eklendi.")
                        else:
                            st.error("Kullanıcı adı zaten var.")

        # Tab 2: Listeleme ve Silme
        with tab2:
            st.subheader("Sistemdeki Kullanıcılar")
            users = database.get_all_users()
            # Pandas DataFrame ile şık tablo gösterimi
            df = pd.DataFrame(users, columns=["Kullanıcı Adı", "Rol"])
            st.dataframe(df, use_container_width=True)
            
            st.divider()
            st.warning("Kullanıcı Silme Alanı")
            user_to_delete = st.selectbox("Silinecek Kullanıcıyı Seçin", [u[0] for u in users])
            if st.button("Seçili Kullanıcıyı Sil"):
                if user_to_delete == "admin":
                    st.error("Ana admin hesabı silinemez!")
                else:
                    database.delete_user(user_to_delete)
                    st.success(f"{user_to_delete} silindi.")
                    time.sleep(1)
                    st.rerun()

    # ---------------- ÖĞRETMEN PANELİ ----------------
    elif st.session_state.user_role == "teacher":
        st.header("📚 Öğretmen Paneli")
        
        tab_duyuru, tab_not = st.tabs(["📢 Duyuru Yap", "📝 Not Girişi"])
        
        # Tab 1: Duyuru Ekleme
        with tab_duyuru:
            with st.form("duyuru_form"):
                st.subheader("Yeni Duyuru Oluştur")
                d_title = st.text_input("Duyuru Başlığı")
                d_content = st.text_area("İçerik")
                submitted = st.form_submit_button("Yayınla")
                if submitted:
                    database.add_announcement(d_title, d_content, st.session_state.username)
                    st.success("Duyuru yayınlandı.")
        
        # Tab 2: Not Girişi
        with tab_not:
            st.subheader("Öğrenci Notu Gir")
            
            # Veritabanından sadece öğrencileri çekiyoruz
            students = database.get_students()
            
            if not students:
                st.warning("Sistemde kayıtlı öğrenci bulunamadı. Lütfen önce Admin panelinden öğrenci ekleyin.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    selected_student = st.selectbox("Öğrenci Seç", students)
                    lesson_name = st.selectbox("Ders", ["Matematik", "Fizik", "Kimya", "Yazılım", "Türkçe"])
                with col2:
                    grade_val = st.number_input("Not", min_value=0, max_value=100, step=1)
                
                if st.button("Notu Kaydet"):
                    database.add_grade(selected_student, lesson_name, grade_val)
                    st.success(f"{selected_student} için not kaydedildi: {grade_val}")

    # ---------------- ÖĞRENCİ PANELİ ----------------
    elif st.session_state.user_role == "student":
        st.header("🎒 Öğrenci Paneli")
        st.info("Bu modül yapım aşamasında. Çok yakında notlarınızı ve duyuruları burada göreceksiniz.")
