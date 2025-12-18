import streamlit as st
import google.generativeai as genai
import json
import time
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Bağarası AI Finans", page_icon="🤖", layout="centered")

# --- STİL ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; }
    .big-font { font-size: 22px !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 1. GOOGLE SHEETS BAĞLANTISI ---
def sonuclari_kaydet(ad, soyad, sinif, puan):
    try:
        # Secrets'tan bilgileri al
        secrets_dict = st.secrets["gcp_service_account"]
        
        # Google'a bağlan
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(secrets_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # Tabloyu aç (Dosya adının 'Okul_Puanlari' olduğundan emin olun)
        sheet = client.open("Okul_Puanlari").sheet1
        
        # Tarih bilgisini al
        tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
        
        # Yeni satır ekle
        yeni_satir = [tarih, f"{ad} {soyad}", sinif, puan]
        sheet.append_row(yeni_satir)
        return True
    except Exception as e:
        st.error(f"Kayıt Hatası: {e}")
        return False

# --- 2. GEMINI AI BAĞLANTISI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

# Yedek Sorular
yedek_sorular = [
    {"soru": "Kasa hesabına para girişi olduğunda hesap nasıl çalışır?", "secenekler": ["Borçlanır", "Alacaklanır", "Kapanır"], "cevap": "Borçlanır"},
    {"soru": "Veresiye mal satışında hangi hesap kullanılır?", "secenekler": ["120 Alıcılar", "320 Satıcılar", "100 Kasa"], "cevap": "120 Alıcılar"}
]

def yapay_zeka_soru_uret():
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = """
        Sen uzman bir Muhasebe Öğretmenisin. Lise öğrencileri için Genel Muhasebe dersiyle ilgili
        5 adet çoktan seçmeli soru hazırla.
        Konular: Kasa, Banka, Çek, Senet, KDV, Mal Alış/Satış, Bilanço.
        
        Çıktıyı SADECE şu JSON formatında ver:
        [
            {
                "soru": "Soru metni",
                "secenekler": ["A", "B", "C"],
                "cevap": "Doğru şıkkın tam metni"
            }
        ]
        Dil: Türkçe.
        """
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        if text_response.startswith("```"):
            text_response = text_response.split("```")[1]
            if text_response.startswith("json"):
                text_response = text_response[4:]
        return json.loads(text_response)
    except:
        return yedek_sorular

# --- OTURUM YÖNETİMİ ---
if 'oturum_basladi' not in st.session_state: st.session_state.oturum_basladi = False
if 'soru_listesi' not in st.session_state: st.session_state.soru_listesi = []
if 'mevcut_soru_index' not in st.session_state: st.session_state.mevcut_soru_index = 0
if 'puan' not in st.session_state: st.session_state.puan = 0
if 'yukleniyor' not in st.session_state: st.session_state.yukleniyor = False
if 'kayit_yapildi' not in st.session_state: st.session_state.kayit_yapildi = False

# --- EKRAN AKIŞI ---
if not st.session_state.oturum_basladi:
    # GİRİŞ EKRANI
    st.title("Bağarası AI Finans Ligi 🤖")
    st.info("Sorular Yapay Zeka tarafından anlık üretilir.")
    
    if st.session_state.yukleniyor:
        with st.status("Sorular Hazırlanıyor...", expanded=True):
            sorular = yapay_zeka_soru_uret()
            st.session_state.soru_listesi = sorular
            st.session_state.oturum_basladi = True
            st.session_state.kayit_yapildi = False
            st.session_state.yukleniyor = False
            st.rerun()
    else:
        with st.form("giris"):
            ad = st.text_input("Ad")
            soyad = st.text_input("Soyad")
            sinif = st.selectbox("Sınıf", ["9-A", "10-A", "11-Muhasebe", "12-Muhasebe"])
            if st.form_submit_button("Başla"):
                if ad and soyad:
                    st.session_state.user_info = {"ad": ad, "soyad": soyad, "sinif": sinif}
                    st.session_state.puan = 0
                    st.session_state.mevcut_soru_index = 0
                    st.session_state.yukleniyor = True
                    st.rerun()

elif st.session_state.mevcut_soru_index < len(st.session_state.soru_listesi):
    # SORU EKRANI
    soru = st.session_state.soru_listesi[st.session_state.mevcut_soru_index]
    st.progress((st.session_state.mevcut_soru_index + 1) / len(st.session_state.soru_listesi))
    st.subheader(soru["soru"])
    
    for secenek in soru["secenekler"]:
        if st.button(secenek, use_container_width=True):
            if secenek == soru["cevap"]:
                st.session_state.puan += 20
                st.toast("✅ Doğru!", icon="🎉")
            else:
                st.toast("❌ Yanlış!", icon="⚠️")
            time.sleep(1)
            st.session_state.mevcut_soru_index += 1
            st.rerun()

else:
    # SONUÇ EKRANI
    st.balloons()
    st.title(f"Sınav Bitti! Puanın: {st.session_state.puan}")
    
    # --- KAYIT İŞLEMİ (OTOMATİK) ---
    if not st.session_state.kayit_yapildi:
        with st.spinner("Puanın Öğretmenine Gönderiliyor..."):
            basari = sonuclari_kaydet(
                st.session_state.user_info["ad"],
                st.session_state.user_info["soyad"],
                st.session_state.user_info["sinif"],
                st.session_state.puan
            )
            if basari:
                st.success("✅ Sonucun Başarıyla Kaydedildi!")
                st.session_state.kayit_yapildi = True
            else:
                st.error("Kayıt sırasında bir hata oluştu.")

    if st.button("Yeni Sınav"):
        st.session_state.oturum_basladi = False
        st.rerun()
