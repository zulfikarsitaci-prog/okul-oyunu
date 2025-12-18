import streamlit as st
import google.generativeai as genai
import json
import time
import random
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Bağarası Sınav Sistemi", page_icon="🎓", layout="centered")

# --- STİL ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; }
    .big-font { font-size: 20px !important; font-weight: 500; }
    </style>
""", unsafe_allow_html=True)

# --- 1. SINIFLARA ÖZEL AYRILMIŞ YEDEK DEPO ---
# (Yapay Zeka çalışmazsa buradan çeker, KARIŞMA OLMAZ)
YEDEK_DEPOLAR = {
    "9": [
        {"soru": "Tacir kime denir?", "secenekler": ["Ticari işletmeyi işleten kimse", "Devlet memuru", "Tüketici"], "cevap": "Ticari işletmeyi işleten kimse"},
        {"soru": "Aşağıdakilerden hangisi ofis programıdır?", "secenekler": ["Excel", "Instagram", "PUBG"], "cevap": "Excel"},
        {"soru": "Etkili iletişimde en önemli unsur nedir?", "secenekler": ["Dinlemek", "Bağırmak", "Kızmak"], "cevap": "Dinlemek"},
        {"soru": "Klavye kısayollarından CTRL+C ne işe yarar?", "secenekler": ["Kopyala", "Yapıştır", "Kes"], "cevap": "Kopyala"},
        {"soru": "Esnaf ve Sanatkarlar Odası kime hitap eder?", "secenekler": ["Küçük işletmelere", "Holdinglere", "Bankalara"], "cevap": "Küçük işletmelere"},
        {"soru": "Word programında dosya uzantısı nedir?", "secenekler": [".docx", ".xlsx", ".pptx"], "cevap": ".docx"},
        {"soru": "Hangisi bir iletişim aracıdır?", "secenekler": ["E-posta", "Hesap Makinesi", "Yazıcı"], "cevap": "E-posta"},
        {"soru": "Excel'de formüller hangi işaretle başlar?", "secenekler": ["=", "?", "#"], "cevap": "="},
        {"soru": "Bilgisayarın beyni olarak bilinen parça hangisidir?", "secenekler": ["İşlemci (CPU)", "Klavye", "Mouse"], "cevap": "İşlemci (CPU)"},
        {"soru": "Hangisi hukukun temel kaynaklarındandır?", "secenekler": ["Anayasa", "Gazete", "Dergi"], "cevap": "Anayasa"}
    ],
    "10": [
        {"soru": "İşletme kasasına para girdiğinde 100 Kasa hesabı nasıl çalışır?", "secenekler": ["Borçlanır", "Alacaklanır", "Kapanır"], "cevap": "Borçlanır"},
        {"soru": "Veresiye mal satışında hangi hesap kullanılır?", "secenekler": ["120 Alıcılar", "320 Satıcılar", "100 Kasa"], "cevap": "120 Alıcılar"},
        {"soru": "Banka hesabından para çekildiğinde 102 Bankalar hesabı ne olur?", "secenekler": ["Alacaklanır", "Borçlanır", "Değişmez"], "cevap": "Alacaklanır"},
        {"soru": "Satıcıya borcumuzu ödediğimizde 320 Satıcılar hesabı nasıl çalışır?", "secenekler": ["Borçlanır", "Alacaklanır", "Bekler"], "cevap": "Borçlanır"},
        {"soru": "Çek düzenleyip satıcıya verdiğimizde hangi hesabı kullanırız?", "secenekler": ["103 Verilen Çekler", "101 Alınan Çekler", "100 Kasa"], "cevap": "103 Verilen Çekler"},
        {"soru": "KDV hariç 100 TL'lik malın %20 KDV'si ne kadardır?", "secenekler": ["20 TL", "18 TL", "10 TL"], "cevap": "20 TL"},
        {"soru": "Aşağıdakilerden hangisi Varlık hesabıdır?", "secenekler": ["100 Kasa", "600 Satışlar", "320 Satıcılar"], "cevap": "100 Kasa"},
        {"soru": "Bilanço denklemi hangisidir?", "secenekler": ["Varlıklar = Kaynaklar", "Gelir = Gider", "Borç = Alacak"], "cevap": "Varlıklar = Kaynaklar"},
        {"soru": "Dönem başı mal mevcudu hangi hesapta izlenir?", "secenekler": ["153 Ticari Mallar", "600 Satışlar", "100 Kasa"], "cevap": "153 Ticari Mallar"},
        {"soru": "Mal alırken ödenen KDV hangi hesaba yazılır?", "secenekler": ["191 İndirilecek KDV", "391 Hesaplanan KDV", "360 Ödenecek Vergi"], "cevap": "191 İndirilecek KDV"}
    ],
    "11": [
        {"soru": "Duran varlıklar bilançonun kaçıncı grubudur?", "secenekler": ["2. Grup", "1. Grup", "3. Grup"], "cevap": "2. Grup"},
        {"soru": "Amortisman hangi varlıklar için ayrılır?", "secenekler": ["Duran Varlıklar", "Dönen Varlıklar", "Borçlar"], "cevap": "Duran Varlıklar"},
        {"soru": "Senetsiz alacaklar şüpheli hale gelirse hangi hesap kullanılır?", "secenekler": ["128 Şüpheli Ticari Alacaklar", "120 Alıcılar", "600 Satışlar"], "cevap": "128 Şüpheli Ticari Alacaklar"},
        {"soru": "Şirket kuruluşunda sermaye taahhüdü kaydında hangi hesap borçlanır?", "secenekler": ["501 Ödenmemiş Sermaye", "500 Sermaye", "100 Kasa"], "cevap": "501 Ödenmemiş Sermaye"},
        {"soru": "Dönem sonunda envanter işlemleri ne için yapılır?", "secenekler": ["Gerçek durumu tespit etmek", "Vergi kaçırmak", "Borçlanmak"], "cevap": "Gerçek durumu tespit etmek"},
        {"soru": "Kıdem tazminatı karşılığı hangi hesapta izlenir?", "secenekler": ["472 Kıdem Tazminatı Karşılığı", "335 Personele Borçlar", "770 Genel Yönetim"], "cevap": "472 Kıdem Tazminatı Karşılığı"},
        {"soru": "Reeskont işlemi hangi hesaplar için yapılır?", "secenekler": ["Senetli Alacak ve Borçlar", "Kasa", "Bankalar"], "cevap": "Senetli Alacak ve Borçlar"},
        {"soru": "Anonim şirketlerde en az sermaye ne kadardır?", "secenekler": ["50.000 TL", "10.000 TL", "5.000 TL"], "cevap": "50.000 TL"},
        {"soru": "Hangisi bir gelir tablosu hesabıdır?", "secenekler": ["600 Yurt İçi Satışlar", "100 Kasa", "255 Demirbaşlar"], "cevap": "600 Yurt İçi Satışlar"},
        {"soru": "Hisse senedi ihraç primleri nerede izlenir?", "secenekler": ["520 Hisse Senedi İhraç Primleri", "600 Satışlar", "642 Faiz"], "cevap": "520 Hisse Senedi İhraç Primleri"}
    ],
    "12": [
        {"soru": "7A seçeneğinde Direkt İlk Madde ve Malzeme gideri kodu nedir?", "secenekler": ["710", "720", "730"], "cevap": "710"},
        {"soru": "Satılan mamulün maliyeti hangi hesapta izlenir?", "secenekler": ["620 Satılan Mamul Maliyeti", "621 Satılan Ticari Mal", "150 İlk Madde"], "cevap": "620 Satılan Mamul Maliyeti"},
        {"soru": "Kurumlar Vergisi oranı (genel) günümüzde yaklaşık ne kadardır?", "secenekler": ["%25", "%10", "%50"], "cevap": "%25"},
        {"soru": "Muhtasar beyanname ne zaman verilir?", "secenekler": ["Takip eden ayın 26'sına kadar", "Her yıl sonunda", "Haftalık"], "cevap": "Takip eden ayın 26'sına kadar"},
        {"soru": "Hangisi bir maliyet unsurudur?", "secenekler": ["Direkt İşçilik", "Kasa Fazlası", "Faiz Geliri"], "cevap": "Direkt İşçilik"},
        {"soru": "Bilanço analizi yaparken 'Cari Oran' formülü nedir?", "secenekler": ["Dönen Varlıklar / Kısa Vadeli Borçlar", "Özkaynak / Borçlar", "Kasa / Banka"], "cevap": "Dönen Varlıklar / Kısa Vadeli Borçlar"},
        {"soru": "İş kazası bildirim süresi kaç gündür?", "secenekler": ["3 İş Günü", "10 Gün", "1 Ay"], "cevap": "3 İş Günü"},
        {"soru": "KDV beyannamesi hangi sıklıkla verilir?", "secenekler": ["Aylık", "Yıllık", "Günlük"], "cevap": "Aylık"},
        {"soru": "Yansıtma hesapları ne işe yarar?", "secenekler": ["Giderleri gelir tablosuna aktarmak", "KDV hesaplamak", "Borç ödemek"], "cevap": "Giderleri gelir tablosuna aktarmak"},
        {"soru": "Geçici vergi dönemleri kaçar aylıktır?", "secenekler": ["3 Ay", "1 Ay", "12 Ay"], "cevap": "3 Ay"}
    ]
}

# --- 2. GEMINI AI BAĞLANTISI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def yapay_zeka_soru_uret(sinif_ham):
    # Sınıf bilgisini sadeleştir (örn: "9-A" -> "9")
    sinif_kodu = "10" # Varsayılan
    if "9" in sinif_ham: sinif_kodu = "9"
    elif "11" in sinif_ham: sinif_kodu = "11"
    elif "12" in sinif_ham: sinif_kodu = "12"
    
    # Konu Belirleme
    konu = "Genel Muhasebe"
    if sinif_kodu == "9": konu = "Mesleki Gelişim, Ofis Programları, Temel Hukuk"
    elif sinif_kodu == "11": konu = "Şirketler Muhasebesi, Envanter, Duran Varlıklar"
    elif sinif_kodu == "12": konu = "Maliyet Muhasebesi, Beyannameler, Analiz"

    ai_sorulari = []
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        # BURADA YAPAY ZEKADAN 10 SORU İSTİYORUZ
        prompt = f"""
        Sen bir Muhasebe Öğretmenisin. {sinif_ham} sınıfı öğrencileri için
        {konu} konularında TAM 10 ADET çoktan seçmeli soru hazırla.
        Zorluk: {sinif_kodu}. Sınıf seviyesine uygun.
        
        ÇIKTI JSON FORMATINDA OLSUN:
        [
            {{ "soru": "...", "secenekler": ["A", "B", "C"], "cevap": "..." }}
        ]
        """
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        if text_response.startswith(""):
            text_response = text_response.split("")[1]
            if text_response.startswith("json"):
                text_response = text_response[4:]
        
        ai_sorulari = json.loads(text_response)
    except Exception as e:
        print(f"AI Hatası: {e}")
        ai_sorulari = []

    # EKSİK VARSA SADECE O SINIFIN DEPOSUNDAN TAMAMLA
    eksik = 10 - len(ai_sorulari)
    if eksik > 0:
        yedekler = YEDEK_DEPOLAR.get(sinif_kodu, YEDEK_DEPOLAR["10"]) # Bulamazsa 10'dan al
        # Yedekleri karıştırıp eksik kadarını al
        eklenecekler = random.sample(yedekler, min(eksik, len(yedekler)))
        ai_sorulari.extend(eklenecekler)
        
    return ai_sorulari[:10] # Garanti 10 soru

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

# GİRİŞ EKRANI
if not st.session_state.oturum_basladi:
    st.image("https://cdn-icons-png.flaticon.com/512/2883/2883857.png", width=100)
    st.title("Bağarası Sınav Sistemi")
    
    if st.session_state.yukleniyor:
        sinif = st.session_state.kimlik["sinif"]
        with st.status(f"{sinif} için 10 Soru Hazırlanıyor...", expanded=True):
            sorular = yapay_zeka_soru_uret(sinif)
            st.session_state.soru_listesi = sorular
            st.session_state.oturum_basladi = True
            st.session_state.kayit_ok = False
            st.session_state.yukleniyor = False
            st.rerun()
    else:
        with st.form("giris"):
            ad = st.text_input("Adınız")
            soyad = st.text_input("Soyadınız")
            sinif = st.selectbox("Sınıfınız", ["9-A", "9-B", "10-A", "10-B", "11-Muhasebe", "12-Muhasebe"])
            if st.form_submit_button("Sınava Başla"):
                if ad and soyad:
                    st.session_state.kimlik = {"ad": ad, "soyad": soyad, "sinif": sinif}
                    st.session_state.puan = 0
                    st.session_state.index = 0
                    st.session_state.yukleniyor = True
                    st.rerun()

# SORU EKRANI
elif st.session_state.index < len(st.session_state.soru_listesi):
    soru = st.session_state.soru_listesi[st.session_state.index]
    toplam = len(st.session_state.soru_listesi)
    
    st.progress((st.session_state.index + 1) / toplam)
    st.write(f"Soru {st.session_state.index + 1} / {toplam}")
    st.markdown(f"<div class='big-font'>{soru['soru']}</div>", unsafe_allow_html=True)
    st.write("")
    
    for sec in soru["secenekler"]:
        if st.button(sec, use_container_width=True):
            if sec == soru["cevap"]:
                st.session_state.puan += 10
                st.toast("✅ Doğru!", icon="🎉")
            else:
                st.toast(f"❌ Yanlış! Cevap: {soru['cevap']}", icon="⚠️")
            time.sleep(1)
            st.session_state.index += 1
            st.rerun()

# SONUÇ EKRANI
else:
    st.balloons()
    st.title(f"Puanın: {st.session_state.puan}")
    st.info(f"{st.session_state.kimlik['ad']} {st.session_state.kimlik['soyad']} - {st.session_state.kimlik['sinif']}")
    
    if not st.session_state.kayit_ok:
        with st.spinner("Kaydediliyor..."):
            res = sonuclari_kaydet(
                st.session_state.kimlik["ad"],
                st.session_state.kimlik["soyad"],
                st.session_state.kimlik["sinif"],
                st.session_state.puan
            )
            if res:
                st.success("Kaydedildi ✅")
                st.session_state.kayit_ok = True
            else:
                st.warning("Kayıt başarısız.")
    
    if st.button("Çıkış"):
        st.session_state.oturum_basladi = False
        st.rerun()
