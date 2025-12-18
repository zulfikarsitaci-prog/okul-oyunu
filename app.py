import streamlit as st
import google.generativeai as genai
import json
import time
import random
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Bağarası ÇPAL Sınav Merkezi", page_icon="🏫", layout="centered")

# --- GÖRÜNTÜ AYARLARI (Karanlık Modu Engelleme) ---
st.markdown("""
    <style>
    /* 1. Ana Arka Planı Zorla BEYAZ Yap */
    .stApp {
        background-color: #ffffff !important;
    }
    
    /* 2. Başlıklar ve Normal Yazıların Hepsini SİYAH Yap */
    h1, h2, h3, h4, h5, h6, p, div, span, label {
        color: #000000 !important;
    }
    
    /* 3. Buton Tasarımı (Net Görünür Gri Kutu, Siyah Yazı) */
    .stButton>button { 
        width: 100%; 
        border-radius: 12px; 
        height: 3.5em; 
        font-weight: bold; 
        background-color: #f0f2f6 !important; 
        color: #000000 !important; 
        border: 2px solid #d1d5db !important;
        transition: all 0.3s;
    }
    
    /* Butonun üzerine gelince hafif koyulaşsın */
    .stButton>button:hover { 
        background-color: #e5e7eb !important; 
        border-color: #000000 !important;
        color: #000000 !important;
    }

    /* 4. Soru Yazısı (Daha Büyük ve Kalın) */
    .big-font { 
        font-size: 24px !important; 
        font-weight: 700; 
        color: #111827 !important; 
        line-height: 1.4;
        margin-bottom: 20px;
    }
    
    /* 5. Giriş Kutuları ve Menülerin İçi */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;
        border-color: #9ca3af !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- DERS MÜFREDATI ---
MUFREDAT = {
    "9. Sınıf": ["Temel Muhasebe", "Mesleki Gelişim Atölyesi", "Mesleki Matematik", "Ofis Uygulamaları"],
    "10. Sınıf": ["Finansal Muhasebe", "Temel Hukuk", "Temel Ekonomi", "Klavye Teknikleri"],
    "11. Sınıf": ["Maliyet Muhasebesi", "Şirketler Muhasebesi", "Bilgisayarlı Muhasebe (Luca)", "Bilgisayarlı Muhasebe (ETA SQL)"],
    "12. Sınıf": ["Bankacılık ve Finans", "Finansal Okuryazarlık"]
}

# --- YEDEK SORU DEPOSU (AI Çalışmazsa) ---
YEDEK_DEPO = {
    "Genel": [
        {"soru": "Tacir, işletmesiyle ilgili işlemleri kaydederken hangi kavrama uymalıdır?", "secenekler": ["Kişilik Kavramı", "Sosyal Sorumluluk", "Dönemsellik"], "cevap": "Kişilik Kavramı"},
        {"soru": "Varlık hesapları (Aktif) artış gösterdiğinde ne yapılır?", "secenekler": ["Borç kaydedilir", "Alacak kaydedilir", "Kapanır"], "cevap": "Borç kaydedilir"}
    ]
}

# --- AI AYARLARI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def yapay_zeka_soru_uret(sinif, ders):
    ai_sorulari = []
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Sen bir Öğretmensin. Hedef: {sinif} öğrencisi, Ders: {ders}.
        Bu ders için 10 adet çoktan seçmeli soru hazırla.
        ÇIKTI FORMATI (SADECE JSON):
        [ {{ "soru": "...", "secenekler": ["A", "B", "C"], "cevap": "..." }} ]
        """
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        if text_response.startswith("```"):
            text_response = text_response.split("```")[1]
            if text_response.startswith("json"):
                text_response = text_response[4:]
        ai_sorulari = json.loads(text_response)
    except:
        ai_sorulari = []

    if len(ai_sorulari) < 10:
        yedek = YEDEK_DEPO["Genel"]
        eksik = 10 - len(ai_sorulari)
        ai_sorulari.extend(random.sample(yedek, min(eksik, len(yedek))))
    
    return ai_sorulari[:10]

# --- KAYIT SİSTEMİ ---
def sonuclari_kaydet(ad, soyad, sinif, ders, puan):
    try:
        if "gcp_service_account" in st.secrets:
            secrets_dict = st.secrets["gcp_service_account"]
            scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_info(secrets_dict, scopes=scope)
            client = gspread.authorize(creds)
            sheet = client.open("Okul_Puanlari").sheet1
            tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
            sheet.append_row([tarih, f"{ad} {soyad}", sinif, ders, puan])
            return True
        return False
    except:
        return False

# --- EKRAN AKIŞI ---
if 'oturum_basladi' not in st.session_state: st.session_state.oturum_basladi = False
if 'soru_listesi' not in st.session_state: st.session_state.soru_listesi = []
if 'index' not in st.session_state: st.session_state.index = 0
if 'puan' not in st.session_state: st.session_state.puan = 0
if 'yukleniyor' not in st.session_state: st.session_state.yukleniyor = False
if 'kayit_ok' not in st.session_state: st.session_state.kayit_ok = False

# 1. GİRİŞ EKRANI
if not st.session_state.oturum_basladi:
    # Başlık Alanı
    st.markdown("<h1 style='text-align: center; color: black;'>Bağarası ÇPAL Sınav Merkezi</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #555;'>Lütfen bilgilerinizi eksiksiz giriniz.</p>", unsafe_allow_html=True)
    
    st.write("### 1. Sınıf ve Ders Seçimi")
    secilen_sinif = st.selectbox("Sınıfınız:", list(MUFREDAT.keys()))
    
    dersler = MUFREDAT[secilen_sinif]
    secilen_ders = st.selectbox("Ders Seçiniz:", dersler)
    
    st.write("### 2. Öğrenci Bilgileri")
    with st.form("giris_formu"):
        col1, col2 = st.columns(2)
        ad = col1.text_input("Adınız")
        soyad = col2.text_input("Soyadınız")
        
        btn = st.form_submit_button("Sınavı Başlat 🚀")
        
        if btn:
            if ad and soyad:
                st.session_state.kimlik = {
                    "ad": ad, "soyad": soyad, 
                    "sinif": secilen_sinif, "ders": secilen_ders
                }
                st.session_state.yukleniyor = True
                st.rerun()
            else:
                st.warning("Lütfen Ad ve Soyad giriniz.")

    if st.session_state.yukleniyor:
        with st.status(f"Lütfen Bekleyiniz... {st.session_state.kimlik['ders']} soruları hazırlanıyor.", expanded=True):
            sorular = yapay_zeka_soru_uret(st.session_state.kimlik['sinif'], st.session_state.kimlik['ders'])
            st.session_state.soru_listesi = sorular
            st.session_state.oturum_basladi = True
            st.session_state.yukleniyor = False
            st.rerun()

# 2. SORU EKRANI
elif st.session_state.index < len(st.session_state.soru_listesi):
    soru = st.session_state.soru_listesi[st.session_state.index]
    toplam = len(st.session_state.soru_listesi)
    
    st.progress((st.session_state.index + 1) / toplam)
    
    # Bilgi satırı
    st.markdown(f"**Ders:** {st.session_state.kimlik['ders']} | **Soru:** {st.session_state.index + 1}/{toplam}")
    
    # Soru
    st.markdown(f"<div class='big-font'>{soru['soru']}</div>", unsafe_allow_html=True)
    
    for sec in soru["secenekler"]:
        if st.button(sec, use_container_width=True):
            if sec == soru["cevap"]:
                st.session_state.puan += 10
                st.toast("✅ Doğru!", icon="🎉")
            else:
                st.toast(f"❌ Yanlış! Cevap: {soru['cevap']}", icon="⚠️")
            time.sleep(1.5)
            st.session_state.index += 1
            st.rerun()

# 3. SONUÇ EKRANI
else:
    st.balloons()
    st.success("Sınav Bitti!")
    
    st.markdown(f"""
    <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center;'>
        <h2 style='color:black; margin:0;'>{st.session_state.kimlik['ad']} {st.session_state.kimlik['soyad']}</h2>
        <h3 style='color:#333;'>Puan: {st.session_state.puan}</h3>
        <p style='color:#555;'>{st.session_state.kimlik['sinif']} - {st.session_state.kimlik['ders']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.kayit_ok:
        with st.spinner("Sonuç kaydediliyor..."):
            res = sonuclari_kaydet(
                st.session_state.kimlik["ad"], st.session_state.kimlik["soyad"],
                st.session_state.kimlik["sinif"], st.session_state.kimlik["ders"],
                st.session_state.puan
            )
            if res:
                st.success("Öğretmene İletildi ✅")
                st.session_state.kayit_ok = True
    
    if st.button("Çıkış Yap"):
        st.session_state.oturum_basladi = False
        st.rerun()
