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

# --- GÖRÜNTÜ AYARLARI (BEYAZ EKRAN ZORLAMA) ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    h1, h2, h3, h4, h5, h6, p, div, span, label, li { color: #000000 !important; }
    .stButton>button { 
        width: 100%; border-radius: 12px; height: auto; padding: 15px;
        font-weight: bold; background-color: #f0f2f6 !important; 
        color: #000000 !important; border: 2px solid #d1d5db !important;
        white-space: pre-wrap; /* Uzun şıklar alt satıra geçsin */
    }
    .stButton>button:hover { background-color: #e5e7eb !important; border-color: #000000 !important; }
    .big-font { font-size: 20px !important; font-weight: 700; color: #111827 !important; margin-bottom: 20px; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #ffffff !important; color: #000000 !important; border-color: #9ca3af !important;
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

# --- YEDEK SORU DEPOSU (AI Çalışmazsa Buradan Çeker - EN AZ 10 SORU GARANTİ) ---
YEDEK_DEPO = {
    "9": [
        {"soru": "Tacir, işletmesiyle ilgili işlemleri kaydederken hangi kavrama uymalıdır?", "secenekler": ["Kişilik Kavramı", "Sosyal Sorumluluk", "Dönemsellik"], "cevap": "Kişilik Kavramı"},
        {"soru": "Word programında metni kopyalamak için hangi kısayol kullanılır?", "secenekler": ["CTRL + C", "CTRL + V", "CTRL + X"], "cevap": "CTRL + C"},
        {"soru": "Aşağıdakilerden hangisi bir iletişim türüdür?", "secenekler": ["Sözlü İletişim", "Bilgisayar", "Yazıcı"], "cevap": "Sözlü İletişim"},
        {"soru": "Excel'de formüller hangi işaretle başlar?", "secenekler": ["=", "?", "!"], "cevap": "="},
        {"soru": "Ticari hayatta güveni sağlayan belge hangisidir?", "secenekler": ["Fatura", "Mektup", "Davetiye"], "cevap": "Fatura"},
        {"soru": "Meslek ahlakına ne ad verilir?", "secenekler": ["Ahilik / Etik", "Esnaflık", "Ticaret"], "cevap": "Ahilik / Etik"},
        {"soru": "Hangisi bir ofis programı değildir?", "secenekler": ["Pubg Mobile", "Word", "Excel"], "cevap": "Pubg Mobile"},
        {"soru": "Yüzde 18 KDV dahil 118 TL olan malın KDV hariç fiyatı nedir?", "secenekler": ["100 TL", "110 TL", "90 TL"], "cevap": "100 TL"},
        {"soru": "Bilgisayarın ana beyni hangisidir?", "secenekler": ["İşlemci (CPU)", "Mouse", "Ekran"], "cevap": "İşlemci (CPU)"},
        {"soru": "Etkili dinleme nasıl olmalıdır?", "secenekler": ["Göz teması kurarak", "Başka yere bakarak", "Söz keserek"], "cevap": "Göz teması kurarak"}
    ],
    "10": [
        {"soru": "Kasa hesabına para girişi olduğunda hesap nasıl çalışır?", "secenekler": ["Borçlanır", "Alacaklanır", "Kapanır"], "cevap": "Borçlanır"},
        {"soru": "Hukuk kurallarına uymamanın yaptırımı nedir?", "secenekler": ["Ceza", "Ödül", "Alkış"], "cevap": "Ceza"},
        {"soru": "İnsan ihtiyaçlarını karşılayan malların üretilmesi faaliyetine ne denir?", "secenekler": ["Ekonomik Faaliyet", "Tüketim", "Hukuk"], "cevap": "Ekonomik Faaliyet"},
        {"soru": "F klavyede temel sıra harfleri hangisidir?", "secenekler": ["UİEAÜTKMLY", "ASDFGHJKL", "QWERTY"], "cevap": "UİEAÜTKMLY"},
        {"soru": "Veresiye mal satışında hangi hesap kullanılır?", "secenekler": ["120 Alıcılar", "320 Satıcılar", "100 Kasa"], "cevap": "120 Alıcılar"},
        {"soru": "Bilanço eşitliği hangisidir?", "secenekler": ["Varlıklar = Kaynaklar", "Gelir = Gider", "Aktif = Kar"], "cevap": "Varlıklar = Kaynaklar"},
        {"soru": "Çek üzerindeki vadeye ne denir?", "secenekler": ["Keşide Tarihi", "Ciro", "İmza"], "cevap": "Keşide Tarihi"},
        {"soru": "Tacir sıfatını kazanmak için ne gerekir?", "secenekler": ["Ticari işletme işletmek", "Memur olmak", "18 yaşını doldurmak"], "cevap": "Ticari işletme işletmek"},
        {"soru": "Mal alımında ödenen KDV hangi hesaba yazılır?", "secenekler": ["191 İndirilecek KDV", "391 Hesaplanan KDV", "360 Ödenecek Vergi"], "cevap": "191 İndirilecek KDV"},
        {"soru": "Enflasyon nedir?", "secenekler": ["Fiyatlar genel düzeyinin sürekli artışı", "Fiyatların düşmesi", "Paranın değer kazanması"], "cevap": "Fiyatlar genel düzeyinin sürekli artışı"}
    ],
    "11": [
        {"soru": "7A seçeneğinde Direkt İlk Madde ve Malzeme Gideri kodu nedir?", "secenekler": ["710", "720", "730"], "cevap": "710"},
        {"soru": "Anonim Şirketlerde en az sermaye tutarı ne kadardır?", "secenekler": ["50.000 TL", "10.000 TL", "500 TL"], "cevap": "50.000 TL"},
        {"soru": "Luca programında yeni fiş oluşturmak için hangi tuş kullanılır?", "secenekler": ["F5 veya Yeni", "F1", "Esc"], "cevap": "F5 veya Yeni"},
        {"soru": "Maliyet muhasebesinin temel amacı nedir?", "secenekler": ["Birim maliyeti saptamak", "Vergi hesaplamak", "Borç ödemek"], "cevap": "Birim maliyeti saptamak"},
        {"soru": "Satılan Mamul Maliyeti hesabı hangisidir?", "secenekler": ["620", "600", "770"], "cevap": "620"},
        {"soru": "Şirketler muhasebesinde sermaye artırımı hangi hesapla izlenir?", "secenekler": ["500 Sermaye", "100 Kasa", "600 Satışlar"], "cevap": "500 Sermaye"},
        {"soru": "Bilgisayarlı muhasebede 'Mizan' neyi gösterir?", "secenekler": ["Hesapların bakiyelerini", "Sadece karı", "Sadece borçları"], "cevap": "Hesapların bakiyelerini"},
        {"soru": "ETA SQL'de şirket açma işlemi hangi modülden yapılır?", "secenekler": ["Sistem Yönetimi", "Muhasebe", "Bordro"], "cevap": "Sistem Yönetimi"},
        {"soru": "Limited şirket en az kaç kişiyle kurulur?", "secenekler": ["1", "2", "5"], "cevap": "1"},
        {"soru": "Amortisman hangi varlıklar için ayrılır?", "secenekler": ["Duran Varlıklar", "Dönen Varlıklar", "Kasa"], "cevap": "Duran Varlıklar"}
    ],
    "12": [
        {"soru": "Bankaların temel fonksiyonu nedir?", "secenekler": ["Fon toplamak ve kullandırmak", "Mal satmak", "İnşaat yapmak"], "cevap": "Fon toplamak ve kullandırmak"},
        {"soru": "Bütçe nedir?", "secenekler": ["Gelecek dönem gelir-gider tahmini", "Geçmişin özeti", "Borç listesi"], "cevap": "Gelecek dönem gelir-gider tahmini"},
        {"soru": "Finansal okuryazarlık neyi ifade eder?", "secenekler": ["Parayı yönetebilme becerisi", "Okuma yazma bilmek", "Zengin olmak"], "cevap": "Parayı yönetebilme becerisi"},
        {"soru": "Bireysel Emeklilik Sistemi (BES) ne işe yarar?", "secenekler": ["Tasarruf ve yatırım sağlar", "Kredi çektirir", "Borç öder"], "cevap": "Tasarruf ve yatırım sağlar"},
        {"soru": "Kredi kartı asgari ödeme tutarı ödenmezse ne olur?", "secenekler": ["Kredi notu düşer", "Puan kazanılır", "Hiçbir şey olmaz"], "cevap": "Kredi notu düşer"},
        {"soru": "Merkez Bankasının temel görevi nedir?", "secenekler": ["Fiyat istikrarını sağlamak", "Konut yapmak", "Araba üretmek"], "cevap": "Fiyat istikrarını sağlamak"},
        {"soru": "Mevduat nedir?", "secenekler": ["Bankaya yatırılan para", "Çekilen kredi", "Ödenen fatura"], "cevap": "Bankaya yatırılan para"},
        {"soru": "Borsada işlem gören kağıtlara ne denir?", "secenekler": ["Hisse Senedi", "Tapu", "Diploma"], "cevap": "Hisse Senedi"},
        {"soru": "Gelir ile gider arasındaki olumlu farka ne denir?", "secenekler": ["Tasarruf", "Borç", "Zarar"], "cevap": "Tasarruf"},
        {"soru": "Faiz nedir?", "secenekler": ["Paranın kullanım bedeli", "Hibe", "Vergi"], "cevap": "Paranın kullanım bedeli"}
    ]
}

# --- AI AYARLARI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def yapay_zeka_soru_uret(sinif, ders):
    ai_sorulari = []
    
    # 1. Aşama: Yapay Zekadan İste
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        # Promptu güçlendirdik: Kesinlikle 10 soru iste
        prompt = f"""
        Sen bir Öğretmensin. Hedef: {sinif} öğrencisi, Ders: {ders}.
        Lütfen bu ders için TAM 10 ADET, çoktan seçmeli, {sinif} seviyesine uygun soru hazırla.
        
        ÇIKTI FORMATI (SADECE VE SADECE JSON OLMALI, BAŞKA YAZI YAZMA):
        [
            {{ "soru": "Soru 1...", "secenekler": ["A", "B", "C"], "cevap": "A" }},
            {{ "soru": "Soru 2...", "secenekler": ["A", "B", "C"], "cevap": "B" }}
        ]
        """
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        
        # JSON Temizliği
        if text_response.startswith("```"):
            text_response = text_response.split("```")[1]
            if text_response.startswith("json"):
                text_response = text_response[4:]
        
        ai_sorulari = json.loads(text_response)
        
    except Exception as e:
        # AI hata verirse boş liste döner, aşağıda yedekten tamamlarız
        print(f"AI Hatası: {e}")
        ai_sorulari = []

    # 2. Aşama: Eğer AI 10 soru vermediyse (veya hiç vermediyse) YEDEKTEN TAMAMLA
    # Sınıf seviyesini bul (9, 10, 11, 12)
    seviye = "10" # Varsayılan
    if "9" in sinif: seviye = "9"
    elif "11" in sinif: seviye = "11"
    elif "12" in sinif: seviye = "12"
    
    yedek_havuz = YEDEK_DEPO.get(seviye, YEDEK_DEPO["10"])
    
    # Eksik sayı kadar yedekten rastgele soru çek
    eksik_sayi = 10 - len(ai_sorulari)
    
    if eksik_sayi > 0:
        # Yedek havuzdan rastgele seç (hata vermemesi için min kontrolü)
        takviye = random.sample(yedek_havuz, min(eksik_sayi, len(yedek_havuz)))
        ai_sorulari.extend(takviye)
    
    # Listeyi karıştır (AI soruları ve Yedek sorular karışsın)
    random.shuffle(ai_sorulari)
    
    # Garanti olsun diye ilk 10 tanesini döndür
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
    # Başlık
    st.markdown("<h1 style='text-align: center; color: black;'>Bağarası ÇPAL Sınav Merkezi</h1>", unsafe_allow_html=True)
    
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
        with st.status(f"Sistem Hazırlanıyor... (Hedef: 10 Soru)", expanded=True):
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
    st.markdown(f"**Ders:** {st.session_state.kimlik['ders']} | **Soru:** {st.session_state.index + 1}/{toplam}")
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
    st.success("Sınav Tamamlandı!")
    
    st.markdown(f"""
    <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #ccc;'>
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
            else:
                st.warning("Otomatik kayıt yapılamadı. Puanınızı öğretmene gösterin.")
    
    if st.button("Çıkış Yap / Yeni Sınav"):
        st.session_state.oturum_basladi = False
        st.rerun()
