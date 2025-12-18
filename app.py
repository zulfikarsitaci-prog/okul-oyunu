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

# --- 1. DEV SORU DEPOSU (YEDEK GÜÇ) ---
# Buraya 100'lerce soru ekleyebilirsiniz. AI çalışmazsa buradan çeker.
YEDEK_DEPO = [
    {"soru": "İşletme kasasından bankaya para yatırıldığında hangi hesap borçlu çalışır?", "secenekler": ["100 Kasa", "102 Bankalar", "103 Verilen Çekler"], "cevap": "102 Bankalar"},
    {"soru": "Veresiye mal satışı yapıldığında alacaklı hesap hangisidir?", "secenekler": ["600 Yurt İçi Satışlar", "120 Alıcılar", "391 Hesaplanan KDV"], "cevap": "600 Yurt İçi Satışlar"},
    {"soru": "İşletmenin borçlarını ödeme gücünü gösteren oranlara ne ad verilir?", "secenekler": ["Likidite Oranları", "Karlılık Oranları", "Faaliyet Oranları"], "cevap": "Likidite Oranları"},
    {"soru": "KDV hariç 1000 TL'lik malın %20 KDV dahil tutarı ne kadardır?", "secenekler": ["1200 TL", "1020 TL", "1180 TL"], "cevap": "1200 TL"},
    {"soru": "Satıcıya olan borcumuzu çek vererek ödedik. Hangi hesap ALACAKLI çalışır?", "secenekler": ["103 Verilen Çekler ve Ödeme Emirleri", "320 Satıcılar", "100 Kasa"], "cevap": "103 Verilen Çekler ve Ödeme Emirleri"},
    {"soru": "Aşağıdakilerden hangisi bir 'Duran Varlık' kalemidir?", "secenekler": ["255 Demirbaşlar", "153 Ticari Mallar", "100 Kasa"], "cevap": "255 Demirbaşlar"},
    {"soru": "Dönem sonunda '600 Yurt İçi Satışlar' hesabı hangi hesaba devredilerek kapatılır?", "secenekler": ["690 Dönem Karı veya Zararı", "500 Sermaye", "100 Kasa"], "cevap": "690 Dönem Karı veya Zararı"},
    {"soru": "Çek üzerindeki vade tarihine ne ad verilir?", "secenekler": ["Keşide Tarihi", "Vade", "Ciro"], "cevap": "Keşide Tarihi"},
    {"soru": "İşletme sahibinin işletmeye koyduğu varlıklara ne denir?", "secenekler": ["Sermaye", "Borç", "Gelir"], "cevap": "Sermaye"},
    {"soru": "Mal alırken ödenen KDV hangi hesapta izlenir?", "secenekler": ["191 İndirilecek KDV", "391 Hesaplanan KDV", "360 Ödenecek Vergi"], "cevap": "191 İndirilecek KDV"},
    {"soru": "Müşteriden alınan senet tahsil edildiğinde hangi hesap ALACAKLI çalışır?", "secenekler": ["121 Alacak Senetleri", "100 Kasa", "102 Bankalar"], "cevap": "121 Alacak Senetleri"},
    {"soru": "Bilanço eşitliği aşağıdakilerden hangisidir?", "secenekler": ["Varlıklar = Kaynaklar", "Varlıklar = Borçlar", "Dönen Varlıklar = Duran Varlıklar"], "cevap": "Varlıklar = Kaynaklar"},
    {"soru": "Bankadaki paramıza faiz tahakkuk ettiğinde (Faiz Geliri), hangi hesap ALACAKLI olur?", "secenekler": ["642 Faiz Gelirleri", "102 Bankalar", "100 Kasa"], "cevap": "642 Faiz Gelirleri"},
    {"soru": "Aşağıdakilerden hangisi Nazım Hesap örneğidir?", "secenekler": ["900 Teminat Mektupları", "100 Kasa", "500 Sermaye"], "cevap": "900 Teminat Mektupları"},
    {"soru": "Satılan malın maliyeti kaydı yapılırken borçlu hesap hangisidir?", "secenekler": ["621 Satılan Ticari Mallar Maliyeti", "153 Ticari Mallar", "600 Yurt İçi Satışlar"], "cevap": "621 Satılan Ticari Mallar Maliyeti"},
    {"soru": "Personele avans verildiğinde hangi hesap kullanılır?", "secenekler": ["196 Personel Avansları", "335 Personele Borçlar", "770 Genel Yönetim Giderleri"], "cevap": "196 Personel Avansları"},
    {"soru": "100 Kasa hesabı ne tür bir bakiyedir?", "secenekler": ["Borç Bakiyesi", "Alacak Bakiyesi", "Bakiye Vermez"], "cevap": "Borç Bakiyesi"},
    {"soru": "Kısa vadeli borçlar bilançonun kaçıncı grubunda yer alır?", "secenekler": ["3. Grup", "4. Grup", "5. Grup"], "cevap": "3. Grup"},
    {"soru": "Hisse senedi ihraç primleri hangi grupta yer alır?", "secenekler": ["Özkaynaklar", "Yabancı Kaynaklar", "Dönen Varlıklar"], "cevap": "Özkaynaklar"},
    {"soru": "Açılış fişinde Pasif hesaplar nasıl kaydedilir?", "secenekler": ["Alacak tarafına", "Borç tarafına", "Kaydedilmez"], "cevap": "Alacak tarafına"},
    {"soru": "Bankadan kredi çekildiğinde '300 Banka Kredileri' hesabı nasıl çalışır?", "secenekler": ["Alacaklanır", "Borçlanır", "Kapanır"], "cevap": "Alacaklanır"},
    {"soru": "Elektrik faturası ödendiğinde genellikle hangi gider hesabı kullanılır?", "secenekler": ["770 Genel Yönetim Giderleri", "760 Pazarlama Giderleri", "153 Ticari Mallar"], "cevap": "770 Genel Yönetim Giderleri"},
    {"soru": "Demirbaş satışından elde edilen kar hangi hesaba yazılır?", "secenekler": ["679 Diğer Olağandışı Gelir ve Karlar", "600 Yurt İçi Satışlar", "642 Faiz Gelirleri"], "cevap": "679 Diğer Olağandışı Gelir ve Karlar"},
    {"soru": "Cari oran hesaplanırken hangi kalemler kullanılır?", "secenekler": ["Dönen Varlıklar / Kısa Vadeli Yabancı Kaynaklar", "Duran Varlıklar / Özkaynaklar", "Kasa / Borçlar"], "cevap": "Dönen Varlıklar / Kısa Vadeli Yabancı Kaynaklar"},
    {"soru": "320 Satıcılar hesabı hangi durumda borçlanır?", "secenekler": ["Satıcıya ödeme yapıldığında", "Mal alındığında", "Senet ciro edildiğinde"], "cevap": "Satıcıya ödeme yapıldığında"}
]

# --- 2. GEMINI AI BAĞLANTISI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def yapay_zeka_soru_uret():
    # Önce AI'dan soru isteyelim
    ai_sorulari = []
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = """
        Sen tecrübeli bir Muhasebe Öğretmenisin.
        Bana Lise düzeyinde Genel Muhasebe dersi için 5 adet ÖZGÜN, ZORLUĞU DENGELİ, çoktan seçmeli soru üret.
        Konular: Yevmiye Kayıtları, Bilanço, KDV Hesaplamaları, Tek Düzen Hesap Planı.
        
        LÜTFEN ÇIKTIYI SADECE AŞAĞIDAKİ JSON FORMATINDA VER:
        [
            {
                "soru": "Soru metni buraya",
                "secenekler": ["A şıkkı", "B şıkkı", "C şıkkı"],
                "cevap": "Doğru olan şıkkın metni"
            }
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

    # EĞER AI AZ SORU ÜRETİRSE VEYA HATA VERİRSE, DEPODAN TAMAMLA
    eksik_sayi = 10 - len(ai_sorulari)
    
    if eksik_sayi > 0:
        # Depodan rastgele soru seçip ekle
        ek_sorular = random.sample(YEDEK_DEPO, min(eksik_sayi, len(YEDEK_DEPO)))
        ai_sorulari.extend(ek_sorular)
        
    # Toplam listeyi karıştır ki AI ve Depo soruları iç içe geçsin
    random.shuffle(ai_sorulari)
    
    # Maksimum 10 soru döndür
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
    st.markdown("**Yapay Zeka** + **Geniş Soru Havuzu** ile güçlendirildi.")
    
    if st.session_state.yukleniyor:
        with st.status("Sorular Hazırlanıyor... (AI + Depo)", expanded=True):
            sorular = yapay_zeka_soru_uret()
            st.session_state.soru_listesi = sorular
            st.session_state.oturum_basladi = True
            st.session_state.kayit_ok = False
            st.session_state.yukleniyor = False
            st.rerun()
    else:
        with st.form("giris"):
            ad = st.text_input("Adınız")
            soyad = st.text_input("Soyadınız")
            sinif = st.selectbox("Sınıf", ["9-A", "10-A", "11-Muhasebe", "12-Muhasebe"])
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
    
    # Seçenekleri karıştır
    secenekler = list(soru["secenekler"])
    # Not: Seçenekleri her seferinde karıştırmak isterseniz burayı açın:
    # random.shuffle(secenekler)

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
    st.info(f"Öğrenci: {st.session_state.kimlik['ad']} {st.session_state.kimlik['soyad']}")
    
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
