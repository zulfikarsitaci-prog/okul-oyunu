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

# --- GÖRÜNTÜ AYARLARI (Beyaz Ekran ve Okunaklı Butonlar) ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    h1, h2, h3, h4, h5, h6, p, div, span, label, li { color: #000000 !important; }
    
    /* Şık Butonları Tasarımı */
    .stButton>button { 
        width: 100%; 
        border-radius: 10px; 
        min-height: 4em; /* Butonlar biraz daha yüksek */
        font-weight: 500; 
        background-color: #f8f9fa !important; 
        color: #000000 !important; 
        border: 2px solid #e9ecef !important;
        white-space: pre-wrap; /* Uzun yazılar alt satıra geçsin */
        text-align: left !important; /* Şıklar sola dayalı olsun */
        padding-left: 20px;
    }
    .stButton>button:hover { 
        background-color: #e2e6ea !important; 
        border-color: #adb5bd !important; 
    }
    
    .big-font { font-size: 22px !important; font-weight: 700; color: #111827 !important; margin-bottom: 25px; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #ffffff !important; color: #000000 !important; border-color: #ced4da !important;
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

# --- YEDEK SORU DEPOSU (5 ŞIKLI VE GÜNCEL) ---
# AI çalışmazsa buradan çeker. Şıklar her seferinde karışır.
YEDEK_DEPO = {
    "Temel Muhasebe": [
        {
            "soru": "Aşağıdakilerden hangisi fatura yerine geçen belgelerden biri DEĞİLDİR?", 
            "secenekler": ["Perakende Satış Fişi", "Serbest Meslek Makbuzu", "Gider Pusulası", "Sevk İrsaliyesi", "Yevmiye Defteri"], 
            "cevap": "Yevmiye Defteri"
        },
        {
            "soru": "Bir malın satışı sırasında, malın sevkiyatı için düzenlenen ve üzerinde fiyat bulunma zorunluluğu olmayan belge hangisidir?", 
            "secenekler": ["Sevk İrsaliyesi", "Fatura", "Gider Pusulası", "Tahsilat Makbuzu", "Çek"], 
            "cevap": "Sevk İrsaliyesi"
        },
        {
            "soru": "İşletme Hesabı Esasına göre defter tutanlar, giderlerini defterin hangi tarafına kaydeder?", 
            "secenekler": ["Gider (Sol) Tarafına", "Gelir (Sağ) Tarafına", "Alt Tarafına", "Arka Sayfaya", "İşletme defterinde gider yazılmaz"], 
            "cevap": "Gider (Sol) Tarafına"
        },
        {
            "soru": "Vergi, resim ve harçların toplanması, tarh ve tahakkuk ettirilmesi hangi kurumun görevidir?", 
            "secenekler": ["Vergi Dairesi", "Belediye", "SGK", "İşkur", "Valilik"], 
            "cevap": "Vergi Dairesi"
        },
        {
            "soru": "İş yeri açma ve çalışma ruhsatı almak için hangi kuruma başvurulur?", 
            "secenekler": ["Belediye", "Maliye Bakanlığı", "Nüfus Müdürlüğü", "Tapu Dairesi", "Emniyet"], 
            "cevap": "Belediye"
        }
    ],
    "Genel": [
        {
            "soru": "KDV (Katma Değer Vergisi) ne tür bir vergidir?", 
            "secenekler": ["Harcama üzerinden alınan vergi", "Gelir üzerinden alınan vergi", "Servet vergisi", "Emlak vergisi", "Motorlu taşıtlar vergisi"], 
            "cevap": "Harcama üzerinden alınan vergi"
        },
        {
            "soru": "Excel programında A1 ile A5 hücreleri arasındaki sayıların ortalamasını alan formül hangisidir?", 
            "secenekler": ["=ORTALAMA(A1:A5)", "=TOPLA(A1:A5)", "=SAY(A1:A5)", "=MİN(A1:A5)", "=MAK(A1:A5)"], 
            "cevap": "=ORTALAMA(A1:A5)"
        },
        {
            "soru": "Bir işletmenin varlıklarının ve borçlarının gösterildiği tabloya ne ad verilir?", 
            "secenekler": ["Bilanço", "Gelir Tablosu", "Mizan", "Kasa Defteri", "Nazım Hesaplar"], 
            "cevap": "Bilanço"
        }
    ]
}

# --- AI AYARLARI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def yapay_zeka_soru_uret(sinif, ders):
    ai_sorulari = []
    
    # 1. GÜNCEL MEVZUAT VE DERS AYARLARI
    konu_detayi = "Güncel 2024-2025 mevzuatına uygun olsun."
    
    if ders == "Temel Muhasebe" and "9" in sinif:
        konu_detayi += " Konular: Belge Düzeni (Fatura, İrsaliye, Gider Pusulası), Vergi Dairesi ve Belediye İşlemleri, Basit Usul, İşletme Defteri."
    elif ders == "Finansal Muhasebe":
        konu_detayi += " Konular: Tek Düzen Hesap Planı, Yevmiye Kayıtları, Bilanço İlkeleri (Bilanço ve Yevmiye sorulabilir)."
    elif "Bilgisayarlı" in ders:
        konu_detayi += " Konular: Program arayüzü, Fiş girişleri, Kısayol tuşları."

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # PROMPT (EMİR): 5 ŞIKLI VE KARIŞIK CEVAPLI
        prompt = f"""
        Rolün: Türkiye Mevzuatına hakim Meslek Lisesi Öğretmeni.
        Ders: {ders} (Sınıf: {sinif}).
        Özel Not: {konu_detayi}
        
        GÖREV: Bu ders için TAM 10 ADET çoktan seçmeli soru hazırla.
        
        KRİTİK KURALLAR:
        1. Her sorunun **5 ADET SEÇENEĞİ** (A,B,C,D,E) olsun.
        2. Doğru cevap şıkkı (A, B, C, D, E) arasında **RASTGELE DAĞILSIN**. Hepsi A olmasın.
        3. Sorular güncel, mantıklı ve düşündürücü olsun.
        4. Çıktı SADECE JSON formatında olsun.
        
        JSON FORMATI:
        [ {{ "soru": "Soru metni...", "secenekler": ["Şık1", "Şık2", "Şık3", "Şık4", "Şık5"], "cevap": "Doğru olan şıkkın tam metni" }} ]
        """
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        
        if text_response.startswith("```"):
            text_response = text_response.split("```")[1]
            if text_response.startswith("json"):
                text_response = text_response[4:]
        
        ai_sorulari = json.loads(text_response)
        
    except Exception as e:
        ai_sorulari = []

    # 2. YEDEK DEPO KONTROLÜ
    if len(ai_sorulari) < 10:
        yedek = YEDEK_DEPO.get(ders, YEDEK_DEPO.get("Genel"))
        eksik = 10 - len(ai_sorulari)
        if yedek:
            eklenecekler = random.choices(yedek, k=eksik)
            ai_sorulari.extend(eklenecekler)
            
    # 3. ZORUNLU KARIŞTIRMA (PYTHON TARAFINDA)
    # AI şıkları hep A yapsa bile, biz burada zorla karıştırıyoruz.
    for soru in ai_sorulari:
        random.shuffle(soru["secenekler"])
    
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
        with st.status(f"Sorular Hazırlanıyor... ({st.session_state.kimlik['ders']})", expanded=True):
            sorular = yapay_zeka_soru_uret(st.session_state.kimlik['sinif'], st.session_state.kimlik['ders'])
            
            if len(sorular) == 0: # Çok nadir hata durumu için koruma
                sorular = YEDEK_DEPO["Genel"]
                
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
    
    # ŞIKLARI LİSTELE
    secenekler = soru["secenekler"]
    # NOT: Zaten fonksiyonda karıştırdık, burada tekrar karıştırmaya gerek yok ama 
    # butonları oluştururken doğru cevabı kontrol etmeliyiz.
    
    for sec in secenekler:
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
