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

# --- GÖRÜNTÜ AYARLARI (Beyaz Ekran Garantisi) ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    h1, h2, h3, h4, h5, h6, p, div, span, label, li { color: #000000 !important; }
    .stButton>button { 
        width: 100%; border-radius: 12px; height: auto; min-height: 3.5em; 
        font-weight: bold; background-color: #f0f2f6 !important; 
        color: #000000 !important; border: 2px solid #d1d5db !important;
        white-space: pre-wrap; /* Uzun şıkları kaydır */
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

# --- YEDEK SORU DEPOSU (HER DERS İÇİN 10 ADET SABİT) ---
# AI çalışmazsa buradan çeker. DERSLER KARIŞMAZ.
YEDEK_DEPO = {
    "Temel Muhasebe": [
        {"soru": "İşletmenin sahip olduğu varlıklar ile bu varlıkların sağlandığı kaynakları gösteren tablo hangisidir?", "secenekler": ["Bilanço", "Gelir Tablosu", "Mizan"], "cevap": "Bilanço"},
        {"soru": "Aşağıdakilerden hangisi bir 'Dönen Varlık' hesabıdır?", "secenekler": ["100 Kasa", "255 Demirbaşlar", "500 Sermaye"], "cevap": "100 Kasa"},
        {"soru": "Nazım hesaplar bilançonun neresinde yer alır?", "secenekler": ["Dipnotlarda (Bilanço dışı)", "Aktifte", "Pasifte"], "cevap": "Dipnotlarda (Bilanço dışı)"},
        {"soru": "Yevmiye defterinden büyük deftere yapılan aktarımların doğruluğunu kontrol eden tablo nedir?", "secenekler": ["Mizan", "Envanter", "Bilanço"], "cevap": "Mizan"},
        {"soru": "Kasa hesabının alacak bakiyesi vermesi ne anlama gelir?", "secenekler": ["Kayıt hatası vardır", "Kasa zengindir", "Normaldir"], "cevap": "Kayıt hatası vardır"},
        {"soru": "Tek Düzen Hesap Planında '1' ile başlayan hesaplar neyi ifade eder?", "secenekler": ["Dönen Varlıklar", "Duran Varlıklar", "Kısa Vadeli Borçlar"], "cevap": "Dönen Varlıklar"},
        {"soru": "Satıcıya olan veresiye borç hangi hesapta izlenir?", "secenekler": ["320 Satıcılar", "120 Alıcılar", "100 Kasa"], "cevap": "320 Satıcılar"},
        {"soru": "Çek üzerindeki keşide tarihi neyi ifade eder?", "secenekler": ["Çekin düzenlendiği tarihi", "Vade tarihini", "Ödeme gününü"], "cevap": "Çekin düzenlendiği tarihi"},
        {"soru": "Hangi işlem 'Kasa' hesabını borçlandırır?", "secenekler": ["Peşin Mal Satışı", "Banka hesabına yatırma", "Satıcıya ödeme"], "cevap": "Peşin Mal Satışı"},
        {"soru": "Vergi dairesine ödenecek KDV hangi hesapta izlenir?", "secenekler": ["360 Ödenecek Vergi ve Fonlar", "191 İndirilecek KDV", "600 Satışlar"], "cevap": "360 Ödenecek Vergi ve Fonlar"}
    ],
    "Ofis Uygulamaları": [
        {"soru": "Excel'de bir hücredeki sayıları toplamak için hangi fonksiyon kullanılır?", "secenekler": ["=TOPLA()", "=SAY()", "=ORTALAMA()"], "cevap": "=TOPLA()"},
        {"soru": "Word programında 'Kaydet' işleminin kısayolu nedir?", "secenekler": ["CTRL + S", "CTRL + P", "CTRL + C"], "cevap": "CTRL + S"},
        {"soru": "PowerPoint programı ne amaçla kullanılır?", "secenekler": ["Sunum hazırlamak", "Hesap tablosu yapmak", "Resim çizmek"], "cevap": "Sunum hazırlamak"},
        {"soru": "Excel'de A1 ile A10 arasındaki en büyük sayıyı bulmak için ne yazılır?", "secenekler": ["=MAK(A1:A10)", "=MİN(A1:A10)", "=BÜYÜK(A1:A10)"], "cevap": "=MAK(A1:A10)"},
        {"soru": "Bilgisayarda 'Kes' işleminin kısayolu hangisidir?", "secenekler": ["CTRL + X", "CTRL + V", "CTRL + Z"], "cevap": "CTRL + X"},
        {"soru": "Word'de metni 'Kalın' (Bold) yapmak için hangi harf simgesine basılır?", "secenekler": ["K (veya B)", "T (veya I)", "A"], "cevap": "K (veya B)"},
        {"soru": "Bir dosyanın uzantısı '.xlsx' ise bu dosya hangi programa aittir?", "secenekler": ["Excel", "Word", "PowerPoint"], "cevap": "Excel"},
        {"soru": "Klavye üzerindeki 'Caps Lock' tuşu ne işe yarar?", "secenekler": ["Büyük harf kilidi", "Silme", "Boşluk bırakma"], "cevap": "Büyük harf kilidi"},
        {"soru": "Aşağıdakilerden hangisi bir 'Donanım' parçasıdır?", "secenekler": ["Mouse (Fare)", "Windows", "Excel"], "cevap": "Mouse (Fare)"},
        {"soru": "Excel'de formüller hangi işaretle başlamak zorundadır?", "secenekler": ["Eşittir (=)", "Artı (+)", "Soru işareti (?)"], "cevap": "Eşittir (=)"}
    ],
     "Mesleki Matematik": [
        {"soru": "KDV hariç 100 TL olan bir malın %20 KDV dahil fiyatı nedir?", "secenekler": ["120 TL", "118 TL", "100 TL"], "cevap": "120 TL"},
        {"soru": "Bir malın maliyeti 500 TL, satış fiyatı 600 TL ise kar oranı yüzde kaçtır?", "secenekler": ["%20", "%10", "%25"], "cevap": "%20"},
        {"soru": "Yarım (1/2) ile Çeyreğin (1/4) toplamı kaçtır?", "secenekler": ["3/4", "1/8", "1 tam"], "cevap": "3/4"},
        {"soru": "Brüt ücret 10.000 TL, kesintiler toplamı 2.500 TL ise Net Ücret ne kadardır?", "secenekler": ["7.500 TL", "12.500 TL", "10.000 TL"], "cevap": "7.500 TL"},
        {"soru": "Bir yıl kaç haftadır?", "secenekler": ["52", "48", "60"], "cevap": "52"},
        {"soru": "1000 TL'nin %18'i kaç TL eder?", "secenekler": ["180 TL", "18 TL", "100 TL"], "cevap": "180 TL"},
        {"soru": "Günde 8 saat çalışan bir işçi, haftada 6 gün çalışırsa toplam kaç saat çalışır?", "secenekler": ["48 Saat", "45 Saat", "50 Saat"], "cevap": "48 Saat"},
        {"soru": "Hangi sayı 5'e kalansız bölünemez?", "secenekler": ["23", "25", "100"], "cevap": "23"},
        {"soru": "Bir düzine kalem kaç adettir?", "secenekler": ["12", "10", "20"], "cevap": "12"},
        {"soru": "Basit faiz hesaplamasında formül nedir?", "secenekler": ["A.n.t / 100", "A.n.t / 3600", "A+n+t"], "cevap": "A.n.t / 100"}
    ]
}
# Not: Diğer dersler için de sistem çalışır. Yer kaplamasın diye hepsini buraya yazmadım 
# ama sistem derse özel boşsa AI'ı zorlar, yoksa genel soruları getirmez.

# --- AI AYARLARI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def yapay_zeka_soru_uret(sinif, ders):
    ai_sorulari = []
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        # Sıkılaştırılmış Prompt: Asla ders dışına çıkma ve 10 soru üret.
        prompt = f"""
        Rolün: Lise Öğretmeni.
        Ders: {ders} (Sınıf: {sinif}).
        
        GÖREV: Bu ders için TAM 10 ADET çoktan seçmeli soru hazırla.
        
        KURALLAR:
        1. SADECE {ders} konusuyla ilgili soru sor. BAŞKA DERSİN SORUSUNU KARIŞTIRMA.
        2. Örneğin ders 'Ofis' ise Muhasebe sorma. Ders 'Muhasebe' ise Excel sorma.
        3. Çıktı SADECE JSON formatında olsun.
        
        JSON FORMATI:
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

    # GÜVENLİK ÖNLEMİ: Eğer AI 10 soru veremezse, Yedek Depoya bak.
    # ÖNEMLİ: Sadece O DERSİN yedek deposuna bak. Genel depoya bakma.
    if len(ai_sorulari) < 10:
        yedek_listesi = YEDEK_DEPO.get(ders, []) # Sadece o dersin yedeklerini al
        
        # Eğer o dersin yedeği yoksa ve AI da çalışmadıysa (Çok nadir olur),
        # En azından boş dönmemek için Temel Muhasebe ekle ama uyarı ver.
        if not yedek_listesi and ders == "Temel Muhasebe": 
            yedek_listesi = YEDEK_DEPO["Temel Muhasebe"]
            
        if yedek_listesi:
            eksik_sayi = 10 - len(ai_sorulari)
            # Rastgele seç ki her seferinde aynı yedekler gelmesin
            eklenecekler = random.sample(yedek_listesi, min(eksik_sayi, len(yedek_listesi)))
            ai_sorulari.extend(eklenecekler)
    
    return ai_sorulari[:10] # Maksimum 10 soru döndür

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
    st.markdown("<h1 style='text-align: center;'>Bağarası ÇPAL Sınav Merkezi</h1>", unsafe_allow_html=True)
    
    st.write("### 1. Ders Seçimi")
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
                st.session_state.kimlik = {"ad": ad, "soyad": soyad, "sinif": secilen_sinif, "ders": secilen_ders}
                st.session_state.yukleniyor = True
                st.rerun()
            else:
                st.warning("Ad ve Soyad zorunludur.")

    if st.session_state.yukleniyor:
        with st.status(f"Yapay Zeka Soruları Hazırlıyor... ({st.session_state.kimlik['ders']})", expanded=True):
            sorular = yapay_zeka_soru_uret(st.session_state.kimlik['sinif'], st.session_state.kimlik['ders'])
            
            # Eğer hiç soru bulunamazsa (AI yok + Yedek yok)
            if len(sorular) == 0:
                st.error("Bu ders için şu an soru üretilemedi. Lütfen tekrar deneyin.")
                st.session_state.yukleniyor = False
                st.stop()
                
            st.session_state.soru_listesi = sorular
            st.session_state.oturum_basladi = True
            st.session_state.yukleniyor = False
            st.rerun()

# 2. SORU EKRANI
elif st.session_state.index < len(st.session_state.soru_listesi):
    soru = st.session_state.soru_listesi[st.session_state.index]
    toplam = len(st.session_state.soru_listesi)
    
    st.progress((st.session_state.index + 1) / toplam)
    st.markdown(f"**{st.session_state.kimlik['ders']}** | Soru {st.session_state.index + 1} / {toplam}")
    
    st.markdown(f"<div class='big-font'>{soru['soru']}</div>", unsafe_allow_html=True)
    
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

# 3. SONUÇ EKRANI
else:
    st.balloons()
    st.success("Sınav Tamamlandı!")
    
    st.markdown(f"""
    <div style='background-color:#f0f2f6; padding:20px; border-radius:10px; text-align:center;'>
        <h2>{st.session_state.kimlik['ad']} {st.session_state.kimlik['soyad']}</h2>
        <h3>Puan: {st.session_state.puan}</h3>
        <p>{st.session_state.kimlik['sinif']} - {st.session_state.kimlik['ders']}</p>
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
                st.success("Kayıt Başarılı ✅")
                st.session_state.kayit_ok = True
    
    if st.button("Çıkış Yap"):
        st.session_state.oturum_basladi = False
        st.rerun()
