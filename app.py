import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import json
import os
import time
import random
import database  # Veritabanı modülümüz
from datetime import datetime

# ==========================================
# 1. SAYFA VE GENEL AYARLAR
# ==========================================
st.set_page_config(
    page_title="Bağarası ÇPAL - Dijital Kampüs",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Veritabanını başlat
database.create_database()
database.add_user("admin", "6626", "admin")

# ==========================================
# 2. HTML / CSS / OYUN SABİTLERİ
# ==========================================
GITHUB_USER = "zulfikarsitaci-prog"
GITHUB_REPO = "s-navkamp-"
GITHUB_BRANCH = "main"
GITHUB_BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}"

URL_LIFESIM = f"{GITHUB_BASE_URL}/lifesim_data.json"
URL_TYT_DATA = f"{GITHUB_BASE_URL}/tyt_data.json"
URL_TYT_PDF = f"{GITHUB_BASE_URL}/tytson8.pdf"
URL_MESLEK_SORULAR = f"{GITHUB_BASE_URL}/sorular.json"

# --- OYUN HTML KODLARI ---
FINANCE_GAME_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<style>
    body { background-color: #0f172a; color: #e2e8f0; font-family: sans-serif; user-select: none; padding: 10px; text-align: center; margin: 0; }
    .dashboard { display: flex; justify-content: space-between; background: #1e293b; padding: 10px; border-radius: 12px; margin-bottom: 20px; }
    .money-val { font-size: 22px; font-weight: 900; color: #34d399; }
    .clicker-btn { background: #3b82f6; border-radius: 50%; width: 100px; height: 100px; font-size: 30px; cursor: pointer; margin: 0 auto 20px auto; display: flex; align-items: center; justify-content: center; }
    .asset-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 8px; }
    .asset-card { background: #1e293b; padding: 8px; border-radius: 8px; cursor: pointer; border: 1px solid #334155; }
    .asset-card:hover { border-color: #facc15; }
    .bank-btn { background: #10b981; color: white; border: none; padding: 8px 20px; border-radius: 6px; cursor: pointer; margin-top: 15px; }
    .code-display { background: white; color: black; padding: 5px; margin-top: 5px; font-weight: bold; display: none; }
</style>
</head>
<body>
    <div class="dashboard">
        <div>NAKİT: <div id="money" class="money-val">0 ₺</div></div>
        <div>GELİR: <div id="cps">0.0 /sn</div></div>
    </div>
    <div class="clicker-btn" onclick="manualWork()">👆</div>
    <div class="asset-grid" id="market"></div>
    <button class="bank-btn" onclick="generateCode()">🏦 Bankaya Aktar</button>
    <div id="transferCode" class="code-display"></div>
<script>
    let money = 0;
    const assets = [
        { name: "Limonata", cost: 150, gain: 0.5, count: 0 }, 
        { name: "Simit Tezgahı", cost: 1000, gain: 3.5, count: 0 },
        { name: "Kantin", cost: 5000, gain: 15.0, count: 0 }, 
        { name: "Yazılım Ofisi", cost: 80000, gain: 200.0, count: 0 }
    ];
    function updateUI() {
        document.getElementById('money').innerText = Math.floor(money).toLocaleString() + ' ₺';
        let totalCps = assets.reduce((t, a) => t + (a.count * a.gain), 0);
        document.getElementById('cps').innerText = totalCps.toFixed(1) + ' /sn';
        const market = document.getElementById('market'); market.innerHTML = '';
        assets.forEach((asset, index) => {
            let currentCost = Math.floor(asset.cost * Math.pow(1.2, asset.count));
            let div = document.createElement('div');
            div.className = 'asset-card';
            div.onclick = () => buyAsset(index);
            div.innerHTML = `<b>${asset.name}</b> (${asset.count})<br><span style="color:#f87171">${currentCost} ₺</span><br><span style="color:#34d399">+${asset.gain}/sn</span>`;
            market.appendChild(div);
        });
    }
    function manualWork() { money += 1; updateUI(); }
    function buyAsset(index) {
        let asset = assets[index]; let currentCost = Math.floor(asset.cost * Math.pow(1.2, asset.count));
        if (money >= currentCost) { money -= currentCost; asset.count++; updateUI(); }
    }
    function generateCode() {
        if (money < 50) { alert("En az 50 ₺ birikmeli."); return; }
        let val = Math.floor(money); let hex = (val * 13).toString(16).toUpperCase(); 
        let rnd = Math.floor(Math.random() * 9999);
        let code = `FNK-${hex}-${rnd}`;
        let box = document.getElementById('transferCode'); box.innerText = code; box.style.display = 'block'; money = 0; updateUI();
    }
    setInterval(() => { let totalCps = assets.reduce((t, a) => t + (a.count * a.gain), 0); if (totalCps > 0) { money += totalCps; updateUI(); } }, 1000);
    updateUI();
</script>
</body>
</html>
"""

ASSET_MATRIX_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<style>
    body { background-color: #050505; color: white; font-family: sans-serif; text-align: center; overflow: hidden; margin: 0; }
    #gameCanvas { background: #111; border: 1px solid #333; margin-top: 10px; }
    .btn { background: #333; color: white; border: 1px solid #555; padding: 10px 20px; cursor: pointer; }
    #bankCodeDisplay { background: white; color: black; padding: 5px; display: none; margin: 10px auto; width: 200px; font-weight: bold;}
</style>
</head>
<body>
    <h3>ASSET MATRIX</h3>
    <div id="score">0</div>
    <button class="btn" onclick="getTransferCode()">🏦 PUANI ÇEK</button>
    <div id="bankCodeDisplay"></div>
    <canvas id="gameCanvas" width="300" height="400"></canvas>
    <script>
        const canvas = document.getElementById('gameCanvas'); const ctx = canvas.getContext('2d');
        let score = 0;
        function draw() {
            ctx.fillStyle = '#111'; ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#3b82f6'; ctx.fillRect(100, 150, 50, 50); // Basit placeholder kare
            ctx.fillStyle = '#fff'; ctx.fillText("Oyun Yüklendi", 110, 100);
        }
        function getTransferCode() {
            // Basit simülasyon puanı
            score += 100; 
            let hex = (score * 13).toString(16).toUpperCase(); 
            let code = `FNK-${hex}-${Math.floor(Math.random()*999)}`;
            document.getElementById('bankCodeDisplay').innerText = code; 
            document.getElementById('bankCodeDisplay').style.display = 'block';
            score = 0;
        }
        draw();
    </script>
</body>
</html>
"""

# ==========================================
# 3. SERVER MANTIĞI (Puan ve Sınıf)
# ==========================================
@st.cache_resource
class SchoolServer:
    def __init__(self):
        # class_code -> { username: points }
        self.classes = {} 
        self.used_codes = set()
        self.create_class("GENEL")

    def create_class(self, class_code):
        if class_code not in self.classes:
            self.classes[class_code] = {}
        return True

    def join_or_update_student(self, class_code, username, points_to_add=0):
        if class_code not in self.classes:
            self.create_class(class_code)
        
        if username not in self.classes[class_code]:
            self.classes[class_code][username] = 0
        
        self.classes[class_code][username] += points_to_add
        return self.classes[class_code][username]

    def get_score(self, class_code, username):
        if class_code in self.classes and username in self.classes[class_code]:
            return self.classes[class_code][username]
        return 0

    def redeem_code(self, class_code, username, code_string):
        if code_string in self.used_codes:
            return False, "Bu kod kullanılmış!"
        try:
            parts = code_string.split('-')
            if len(parts) != 3 or parts[0] != "FNK": return False, "Geçersiz kod!"
            hex_val = parts[1]
            amount = int(int(hex_val, 16) / 13)
            self.used_codes.add(code_string)
            new_balance = self.join_or_update_student(class_code, username, amount)
            return True, new_balance
        except: return False, "Hata oluştu."

    def get_leaderboard(self, class_code):
        if class_code in self.classes:
            data = [{"Öğrenci": k, "Puan": v} for k, v in self.classes[class_code].items()]
            if data:
                return pd.DataFrame(data).sort_values(by="Puan", ascending=False)
        return pd.DataFrame()

server = SchoolServer()

# Yardımcılar
@st.cache_data(ttl=300)
def fetch_json_data(url):
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else {}
    except: return {}

def load_lifesim():
    try:
        r = requests.get(f"{GITHUB_BASE_URL}/game.html")
        html = r.text if r.status_code == 200 else "<h3>Yüklenemedi</h3>"
        data = fetch_json_data(URL_LIFESIM)
        json_str = json.dumps(data if data else [])
        return html.replace("// PYTHON_DATA_HERE", f"var scenarios = {json_str};")
    except: return "Hata"

# ==========================================
# 4. ARAYÜZ MANTIĞI
# ==========================================

# Oturum Kontrolleri
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_role" not in st.session_state: st.session_state.user_role = None
if "username" not in st.session_state: st.session_state.username = None
if "class_code" not in st.session_state: st.session_state.class_code = "GENEL"

# --- GİRİŞ EKRANI (TEK VE ORTAK) ---
if not st.session_state.logged_in:
    st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <h1>🎓 Bağarası ÇPAL</h1>
        <h3>Dijital Kampüs Girişi</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_master"):
            user_inp = st.text_input("Kullanıcı Adı / Okul No")
            pass_inp = st.text_input("Şifre", type="password")
            submitted = st.form_submit_button("Giriş Yap", use_container_width=True)
            
            if submitted:
                user = database.login_user(user_inp, pass_inp)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_role = user[3] # admin, teacher, student
                    st.session_state.username = user[1]
                    
                    # Öğrenciyse başlangıç puanını server'a tanıt
                    if user[3] == "student":
                        server.join_or_update_student("GENEL", user[1], 0)
                        
                    st.success("Giriş Başarılı!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Kullanıcı adı veya şifre hatalı!")
        
        st.info("Hesabınız yoksa yöneticinizle iletişime geçin.")

# --- İÇERİK EKRANLARI (ROL TABANLI) ---
else:
    # Sidebar: Kullanıcı Bilgisi ve Çıkış
    with st.sidebar:
        st.write(f"👤 **{st.session_state.username}**")
        st.caption(f"Yetki: {st.session_state.user_role.upper()}")
        
        # Eğer öğrenciyse, hangi sınıfta (Leaderboard için) olduğunu seçebilir
        if st.session_state.user_role == "student":
            st.divider()
            code_input = st.text_input("Sınıf Kodu Gir", placeholder="Örn: 1234")
            if st.button("Sınıfa Geç"):
                st.session_state.class_code = code_input
                server.join_or_update_student(code_input, st.session_state.username)
                st.success(f"Sınıf: {code_input}")
                st.rerun()
        
        st.divider()
        if st.button("Çıkış Yap", type="primary"):
            st.session_state.logged_in = False
            st.rerun()

    # ----------------------------------------
    # SENARYO 1: ADMIN (YÖNETİM PANELİ)
    # ----------------------------------------
    if st.session_state.user_role == "admin":
        st.header("⚙️ Yönetici Paneli")
        
        tab1, tab2 = st.tabs(["Kullanıcı Ekle", "Kullanıcı Listesi"])
        with tab1:
            st.subheader("Yeni Hesap Oluştur")
            with st.form("add_user"):
                u_name = st.text_input("Kullanıcı Adı (Örn: ali123)")
                u_pass = st.text_input("Şifre")
                u_role = st.selectbox("Rol", ["student", "teacher", "admin"])
                if st.form_submit_button("Kaydet"):
                    if database.add_user(u_name, u_pass, u_role):
                        st.success("Kullanıcı oluşturuldu.")
                    else:
                        st.error("Bu kullanıcı zaten var.")
        
        with tab2:
            st.subheader("Kayıtlı Kullanıcılar")
            users = database.get_all_users()
            df = pd.DataFrame(users, columns=["Kullanıcı", "Rol"])
            st.dataframe(df, use_container_width=True)
            
            to_del = st.selectbox("Silinecek Kişi", df["Kullanıcı"])
            if st.button("Sil"):
                if to_del != "admin":
                    database.delete_user(to_del)
                    st.rerun()
                else: st.error("Admin silinemez.")

    # ----------------------------------------
    # SENARYO 2: ÖĞRETMEN PANELİ
    # ----------------------------------------
    elif st.session_state.user_role == "teacher":
        st.header("👨‍🏫 Öğretmen Paneli")
        
        # Sınıf Kodu Oluşturma
        if "created_code" not in st.session_state:
            st.session_state.created_code = str(random.randint(1000, 9999))
            server.create_class(st.session_state.created_code)
            
        st.info(f"Aktif Ders Kodunuz: **{st.session_state.created_code}** (Öğrencilerle paylaşın)")
        
        tab1, tab2 = st.tabs(["Liderlik Tablosu", "Duyuru Ekle"])
        
        with tab1:
            st.subheader("Sınıf Sıralaması")
            if st.button("Yenile"): st.rerun()
            df = server.get_leaderboard(st.session_state.created_code)
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("Henüz bu derse katılan öğrenci yok.")
                
        with tab2:
            with st.form("ann_form"):
                baslik = st.text_input("Başlık")
                icerik = st.text_area("Mesajınız")
                if st.form_submit_button("Yayınla"):
                    database.add_announcement(baslik, icerik, st.session_state.username)
                    st.success("Duyuru gönderildi.")

    # ----------------------------------------
    # SENARYO 3: ÖĞRENCİ (DİJİTAL KAMPÜS)
    # ----------------------------------------
    elif st.session_state.user_role == "student":
        # Üst Bilgi Barı
        puan = server.get_score(st.session_state.class_code, st.session_state.username)
        col_a, col_b, col_c = st.columns([2, 1, 1])
        with col_a:
            st.title(f"Merhaba, {st.session_state.username}")
        with col_b:
            st.metric("Sınıf", st.session_state.class_code)
        with col_c:
            st.metric("Kampüs Puanı", f"{puan} ₺")

        # Ana Kampüs Sekmeleri
        tab_main, tab_lessons, tab_games, tab_life = st.tabs(["🏆 Kampüs Meydanı", "📚 Dersler & Test", "🎮 Oyun Alanı", "💼 Kariyer Sim"])

        with tab_main:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown("### 🏦 Puan Yükle")
                st.caption("Oyunlardan kazandığın kodu buraya gir.")
                code_in = st.text_input("Kod:", key="code_redeem")
                if st.button("Bozdur ve Yükle"):
                    status, msg = server.redeem_code(st.session_state.class_code, st.session_state.username, code_in)
                    if status:
                        st.success(f"Başarılı! Yeni Puan: {msg}")
                        time.sleep(1); st.rerun()
                    else:
                        st.error(msg)
                
                st.divider()
                st.markdown("### 📢 Duyurular")
                anns = database.get_announcements()
                if anns:
                    for a in anns:
                        with st.expander(f"{a[1]} - {a[4]}"):
                            st.write(a[2])
                else: st.info("Duyuru yok.")

            with c2:
                st.markdown("### 🏅 Sınıf Sıralaması")
                df = server.get_leaderboard(st.session_state.class_code)
                st.dataframe(df, use_container_width=True)

        with tab_lessons:
            st.write("Ders materyalleri ve testler burada.")
            # Buraya TYT / Soru modüllerini entegre edebilirsiniz
            # Örnek PDF gösterimi:
            st.markdown(f'<iframe src="{URL_TYT_PDF}" width="100%" height="600px"></iframe>', unsafe_allow_html=True)

        with tab_games:
            secim = st.selectbox("Oyun Seç:", ["Finans İmparatoru (Clicker)", "Asset Matrix (Tetris Finans)"])
            if "Finans" in secim:
                components.html(FINANCE_GAME_HTML, height=600)
            else:
                components.html(ASSET_MATRIX_HTML, height=600)

        with tab_life:
            st.info("Hayat Simülasyonu Yükleniyor...")
            components.html(load_lifesim(), height=800, scrolling=True)
