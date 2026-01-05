# Öğretmen Paneli
elif st.session_state.user_role == "teacher":
    st.header("Öğretmen Paneli")
    st.write("Ders programları ve öğrenci notlarını buradan yönetebilirsiniz.")
    tab1, tab2 = st.tabs(["Ders Programları", "Öğrenci Notları"])
    with tab1:
        st.subheader("Ders Programları")
        with st.form("add_lesson_form"):
            lesson_name = st.text_input("Ders Adı")
            lesson_time = st.text_input("Ders Saati")
            lesson_day = st.selectbox("Ders Günü", ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"])
            submitted = st.form_submit_button("Ders Ekle")
            if submitted:
                database.add_lesson(lesson_name, lesson_time, lesson_day)
                st.success("Ders eklendi")
        lessons = database.get_lessons()
        for lesson in lessons:
            st.write(f"{lesson[1]} - {lesson[2]} - {lesson[3]}")
    with tab2:
        st.subheader("Öğrenci Notları")
        with st.form("add_grade_form"):
            student_name = st.text_input("Öğrenci Adı")
            lesson_name = st.text_input("Ders Adı")
            grade = st.text_input("Not")
            submitted = st.form_submit_button("Not Ekle")
            if submitted:
                database.add_grade(student_name, lesson_name, grade)
                st.success("Not eklendi")
        grades = database.get_grades()
        for grade in grades:
            st.write(f"{grade[1]} - {grade[2]} - {grade[3]}")

# Admin Paneli
elif st.session_state.user_role == "admin":
    st.header("Admin Paneli")
    st.info("Sistem yönetimi ve kullanıcı işlemleri.")
    tab1, tab2 = st.tabs(["Kullanıcı Yönetimi", "Sistem Ayarları"])
    with tab1:
        st.subheader("Kullanıcı Yönetimi")
        users = database.get_users()
        for user in users:
            st.write(f"{user[1]} - {user[3]}")
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
    with tab2:
        st.subheader("Sistem Ayarları")
        st.write("Sistem ayarları buradan yönetilebilir.")