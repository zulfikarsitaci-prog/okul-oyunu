import streamlit as st
import google.generativeai as genai
import json
import time
import random
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Bağarası AI Finans", page_icon="🎓", layout="centered")

# --- STİL ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; }
    .big-font { font-size: 20px !important; font-weight: 500; }
    </style>
""", unsafe_allow_html=True)

# --- 1. YEDEK DEPO (İNTERNET KOPARSA HERKESE ORTAK SORULAR) ---
YEDEK_DEPO = [
    {"soru": "İşletme kasasından bankaya para yatırıldığında hangi hesap borçlu çalışır?", "secenekler": ["100 Kasa", "102 Bankalar", "103 Verilen Çekler"], "cevap": "102 Bankalar"},
    {"soru": "Veresiye mal satışı yapıldığında alacaklı hesap hangisidir?", "secenekler": ["600 Yurt İçi Satışlar", "120 Alıcılar", "391 Hesaplanan KDV"], "cevap": "600 Yurt İçi Satışlar"},
    {"soru": "Satıcıya olan borcumuzu çek vererek ödedik. Hangi hesap ALACAKLI çalışır?", "secenekler": ["103 Verilen Çekler", "320 Satıcılar", "100 Kasa"], "cevap": "103 Verilen Çekler"},
    {"soru": "Aşağıdakilerden hangisi bir 'Duran Varlık' kalemidir?", "secenekler": ["255 Demirbaşlar", "153 Ticari Mallar", "100 Kasa"], "cevap": "255 Demirbaşlar"},
    {"soru": "KDV hariç 1000 TL'lik malın %20 KDV dahil tutarı ne kadardır?", "secenekler": ["1200 TL", "1020 TL", "1180 TL"], "cevap": "1200 TL"}
]

# --- 2. GEMINI AI BAĞLANTISI (AKILLI ÖĞRETMEN MODU) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def yapay_zeka_soru_uret(sinif_seviyesi):
    # Sınıfa göre konu belirleme mantığı
    konu_kapsami = "Genel Muhasebe"
    zorluk = "Orta"
    
    if "9" in sinif_seviyesi:
        konu_kapsami = "Mesleki Gelişim, Temel Hukuk Bilgisi, Ofis Programları, Tacir/Esnaf Kavramları"
        zorluk = "Başlangıç (Kolay)"
    elif "10" in sinif_seviyesi:
        konu_kapsami = "Genel Muhasebe 1, Yevmiye Kayıtları, Büyük Defter, Mizan, Varlık Hesapları (Kasa, Banka, Çek)"
        zorluk = "Orta"
    elif "11" in sinif_seviyesi:
        konu_kapsami = "Dönem Sonu İşlemleri, Envanter, Şirketler Muhasebesi, Bilgisayarlı Muhasebe, Duran Varlıklar"
        zorluk = "İleri"
    elif "12" in sinif_seviyesi:
        konu_kapsami = "Maliyet Muhasebesi (7A/7B), Beyannameler, Mali Tablolar Analizi, İş ve Sosyal Güvenlik Hukuku"
        zorluk = "Zor/Uzman"

    ai_sorulari = []
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Sen Türkiye müfredatına hakim uzman bir Muhasebe Öğretmenisin.
        Şu an sınava giren öğrenci seviyesi: **{sinif_seviyesi}**.
        
        Lütfen bu seviyeye uygun, **{zorluk}** zorluk derecesinde, şu konulardan 5 adet çoktan seçmeli soru hazırla:
        **{konu_kapsami}**
        
        ÇIKTIYI SADECE AŞAĞIDAKİ JSON FORMATINDA VER (Başka açıklama yapma):
        [
            {{
                "soru": "Soru metni",
                "secenekler": ["A", "B", "C"],
                "cevap": "Doğru şıkkın aynısı"
            }}
        ]
        """
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        if text_response.startswith("```"):
            text_response = text_response.split("```")[1]
            if text_response.startswith("json"):
                text_response = text_response[4:]
        
        ai_sorulari = json.loads(text_response)
    except Exception as e:
        print(f"AI Hatası: {e}")
        ai_sorulari = []

    # Eğer AI hata verirse veya az soru üretirse depodan tamamla
    eksik_sayi = 10 - len(ai_sorulari)
    if eksik_sayi > 0:
        ek_sorular = random.sample(YEDEK_DEPO, min(eksik_sayi, len(YEDEK_DEPO)))
        ai_sorulari.extend(ek_sorular)
        
    random.shuffle(ai_sorulari)
    return ai_sorulari[:10]

# --- 3. GOOGLE SHEETS KAYIT ---
def sonuclari_kaydet(ad, soyad, sinif, puan):
    try:
        if "gcp_service_account" in st.secrets:
            secrets_dict = st.secrets["gcp_service_account"]
            scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_info(secrets_dict, scopes=scope)
            client = gspread.authorize(creds)
            sheet = client.open("Okul_Puanlari").sheet1
            tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
            sheet.append_row([tarih, f"{ad} {soyad}", sinif, puan])
            return True
        return False
    except Exception as e:
        st.error(f"Kayıt Hatası: {e}")
        return False

# --- EKRAN YÖNETİMİ ---
if 'oturum_basladi' not in st.session_state: st.session_state.oturum_basladi = False
if 'soru_listesi' not in st.session_state: st.session_state.soru_listesi = []
if 'index' not in st.session_state: st.session_state.index = 0
if 'puan' not in st.session_state: st.session_state.puan = 0
if 'yukleniyor' not in st.session_state: st.session_state.yukleniyor = False
if 'kayit_ok' not in st.session_state: st.session_state.kayit_ok = False

# 1. GİRİŞ EKRANI
if not st.session_state.oturum_basladi:
    st.image("https://cdn-icons-png.flaticon.com/512/2883/2883857.png", width=100)
    st.title("Bağarası Hibrit Sınav Sistemi")
    st.info("Sorular sınıf seviyenize (9-10-11-12) göre özel olarak hazırlanacaktır.")
    
    if st.session_state.yukleniyor:
        secilen_sinif = st.session_state.kimlik["sinif"]
        with st.status(f"Yapay Zeka {secilen_sinif} seviyesine uygun sorular hazırlıyor...", expanded=True):
            sorular = yapay_zeka_soru_uret(secilen_sinif)
            st.session_state.soru_listesi = sorular
            st.session_state.oturum_basladi = True
            st.session_state.kayit_ok = False
            st.session_state.yukleniyor = False
            st.rerun()
    else:
        with st.form("giris"):
            ad = st.text_input("Adınız")
            soyad = st.text_input("Soyadınız")
            # Sınıf listesini buradan güncelleyebilirsiniz
            sinif = st.selectbox("Sınıfınız", ["9-A", "9-B", "10-A", "10-B", "11-Muhasebe", "12-Muhasebe"])
            
            if st.form_submit_button("Sınavı Başlat"):
                if ad and soyad:
                    st.session_state.kimlik = {"ad": ad, "soyad": soyad, "sinif": sinif}
                    st.session_state.puan = 0
                    st.session_state.index = 0
                    st.session_state.yukleniyor = True
                    st.rerun()

# 2. SORU EKRANI
elif st.session_state.index < len(st.session_state.soru_listesi):
    soru = st.session_state.soru_listesi[st.session_state.index]
    toplam = len(st.session_state.soru_listesi)
    
    st.progress((st.session_state.index + 1) / toplam)
    st.write(f"Soru {st.session_state.index + 1} / {toplam}")
    st.markdown(f"<div class='big-font'>{soru['soru']}</div>", unsafe_allow_html=True)
    st.write("")
    
    secenekler = list(soru["secenekler"])
    
    for sec in secenekler:
        if st.button(sec, use_container_width=True):
            if sec == soru["cevap"]:
                st.session_state.puan += 10
                st.toast("✅ Doğru!", icon="🎉")
            else:
                st.toast(f"❌ Yanlış! Cevap: {soru['cevap']}", icon="⚠️")
            time.sleep(1)
            st.session_state.index += 1
            st.rerun()

# 3. SONUÇ EKRANI
else:
    st.balloons()
    st.title(f"Puanın: {st.session_state.puan}")
    st.info(f"Öğrenci: {st.session_state.kimlik['ad']} {st.session_state.kimlik['soyad']} ({st.session_state.kimlik['sinif']})")
    
    if not st.session_state.kayit_ok:
        with st.spinner("Sonuç kaydediliyor..."):
            sonuc = sonuclari_kaydet(
                st.session_state.kimlik["ad"],
                st.session_state.kimlik["soyad"],
                st.session_state.kimlik["sinif"],
                st.session_state.puan
            )
            if sonuc:
                st.success("Sonuç Öğretmenine İletildi! ✅")
                st.session_state.kayit_ok = True
            else:
                st.warning("Kayıt yapılamadı (Bağlantı sorunu olabilir).")

    if st.button("Çıkış / Yeni Sınav"):
        st.session_state.oturum_basladi = False
        st.rerun()
