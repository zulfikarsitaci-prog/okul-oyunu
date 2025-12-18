import streamlit as st
import google.generativeai as genai
import json
import time

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Bağarası AI Finans", page_icon="🤖", layout="centered")

# --- STİL ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; }
    .big-font { font-size: 22px !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- API ANAHTARI KONTROLÜ ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı! Lütfen Streamlit Secrets ayarlarını yapın.")
    st.stop()

# --- YEDEK SORU HAVUZU (Acil Durumlar İçin) ---
yedek_sorular = [
    {"soru": "Kasa hesabına para girişi olduğunda hesap nasıl çalışır?", "secenekler": ["Borçlanır", "Alacaklanır", "Kapanır"], "cevap": "Borçlanır"},
    {"soru": "Veresiye mal satışında hangi hesap kullanılır?", "secenekler": ["120 Alıcılar", "320 Satıcılar", "100 Kasa"], "cevap": "120 Alıcılar"},
    {"soru": "Satıcıya borcumuzu ödersek 320 Satıcılar hesabı ne olur?", "secenekler": ["Borçlanır (Azalır)", "Alacaklanır (Artar)", "Değişmez"], "cevap": "Borçlanır (Azalır)"},
    {"soru": "Hangisi bir varlık hesabıdır?", "secenekler": ["100 Kasa", "600 Satışlar", "320 Satıcılar"], "cevap": "100 Kasa"},
    {"soru": "KDV hangi hesapta takip edilmez?", "secenekler": ["600 Yurt İçi Satışlar", "191 İndirilecek KDV", "391 Hesaplanan KDV"], "cevap": "600 Yurt İçi Satışlar"}
]

# --- YAPAY ZEKA FONKSİYONU ---
def yapay_zeka_soru_uret():
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = """
        Sen uzman bir Muhasebe Öğretmenisin. Lise öğrencileri için Genel Muhasebe dersiyle ilgili
        5 adet çoktan seçmeli soru hazırla. Sorular ne çok kolay ne çok zor olsun.
        Konular: Kasa, Banka, Çek, Senet, KDV, Mal Alış/Satış, Bilanço Esasları.
        
        Çıktıyı SADECE şu JSON formatında ver, başka hiçbir açıklama yazma:
        [
            {
                "soru": "Soru metni buraya",
                "secenekler": ["A şıkkı", "B şıkkı", "C şıkkı"],
                "cevap": "Doğru olan şıkkın aynısı"
            }
        ]
        Dil: Türkçe. Türkiye Tek Düzen Hesap Planına uygun olsun.
        """
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        
        # JSON temizliği
        if text_response.startswith("```"):
            text_response = text_response.split("```")[1]
            if text_response.startswith("json"):
                text_response = text_response[4:]
        
        return json.loads(text_response)
    except Exception as e:
        return yedek_sorular

# --- OTURUM AYARLARI ---
if 'oturum_basladi' not in st.session_state:
    st.session_state.oturum_basladi = False
if 'soru_listesi' not in st.session_state:
    st.session_state.soru_listesi = []
if 'mevcut_soru_index' not in st.session_state:
    st.session_state.mevcut_soru_index = 0
if 'puan' not in st.session_state:
    st.session_state.puan = 0
if 'yukleniyor' not in st.session_state:
    st.session_state.yukleniyor = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = {}

# --- FONKSİYONLAR ---
def sinavi_baslat(ad, soyad, sinif):
    st.session_state.user_info = {"ad": ad, "soyad": soyad, "sinif": sinif}
    st.session_state.yukleniyor = True
    st.rerun()

def cevap_ver(secilen, dogru_cevap):
    if secilen == dogru_cevap:
        st.session_state.puan += 20
        st.toast("✅ Doğru! (+20 Puan)", icon="🎉")
    else:
        st.toast(f"❌ Yanlış! Doğrusu: {dogru_cevap}", icon="⚠️")
    
    time.sleep(1.5)
    
    if st.session_state.mevcut_soru_index + 1 < len(st.session_state.soru_listesi):
        st.session_state.mevcut_soru_index += 1
        st.rerun()
    else:
        st.session_state.sinav_bitti = True
        st.rerun()

def yeniden_baslat():
    st.session_state.oturum_basladi = False
    st.session_state.sinav_bitti = False
    st.session_state.yukleniyor = False
    st.session_state.puan = 0
    st.rerun()

# --- EKRAN AKIŞI ---
if not st.session_state.oturum_basladi:
    # GİRİŞ EKRANI
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=80)
    st.title("Bağarası AI Finans Ligi 🤖")
    st.write("Yapay Zeka (Gemini) senin için özel sorular hazırlıyor...")
    
    if st.session_state.yukleniyor:
        with st.status("🧠 Yapay Zeka Soruları Hazırlıyor...", expanded=True) as status:
            st.write("Muhasebe veritabanı taranıyor...")
            time.sleep(1)
            st.write("Gemini ile bağlantı kuruluyor...")
            # --- AI BURADA ÇALIŞIYOR ---
            sorular = yapay_zeka_soru_uret()
            # ---------------------------
            st.session_state.soru_listesi = sorular
            status.update(label="Sorular Hazır! Başarılar...", state="complete", expanded=False)
            time.sleep(1)
            st.session_state.oturum_basladi = True
            st.session_state.sinav_bitti = False
            st.session_state.yukleniyor = False
            st.rerun()
            
    else:
        with st.form("giris_formu"):
            ad = st.text_input("Adınız")
            soyad = st.text_input("Soyadınız")
            sinif = st.selectbox("Sınıfınız", ["9-A", "10-A", "11-Muhasebe", "12-Muhasebe", "Öğretmen"])
            submit = st.form_submit_button("Sınavı Başlat 🚀")
            
            if submit:
                if ad and soyad:
                    sinavi_baslat(ad, soyad, sinif)
                else:
                    st.warning("Lütfen isminizi giriniz.")

elif not st.session_state.sinav_bitti:
    # SORU EKRANI
    soru_data = st.session_state.soru_listesi[st.session_state.mevcut_soru_index]
    toplam = len(st.session_state.soru_listesi)
    suanki = st.session_state.mevcut_soru_index + 1
    
    st.progress(suanki / toplam)
    st.caption(f"Soru {suanki}/{toplam} | {st.session_state.user_info['ad']} {st.session_state.user_info['soyad']}")
    
    st.markdown(f"<div class='big-font'>{soru_data['soru']}</div>", unsafe_allow_html=True)
    st.write("")
    
    for secenek in soru_data["secenekler"]:
        if st.button(secenek, use_container_width=True):
            cevap_ver(secenek, soru_data["cevap"])

else:
    # SONUÇ EKRANI
    st.balloons()
    st.title("🏁 Sınav Bitti!")
    
    st.divider()
    col1, col2 = st.columns(2)
    col1.metric("Öğrenci", f"{st.session_state.user_info['ad']}")
    col2.metric("PUAN", f"{st.session_state.puan}")
    
    st.divider()
    
    if st.session_state.puan >= 80:
        st.success("Tebrikler! Yapay zekayı alt ettin. 🦾")
    elif st.session_state.puan >= 50:
        st.warning("Güzel sonuç, ama daha iyisi olabilir.")
    else:
        st.error("Biraz daha çalışman lazım.")
        
    if st.button("🔄 Yeni Sorularla Tekrar Dene"):
        yeniden_baslat()
