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

# --- GÖRÜNTÜ AYARLARI (SARI ZEMİN - SİYAH YAZI) ---
st.markdown("""
    <style>
    /* 1. Arka Planı SARI Yap */
    .stApp {
        background-color: #FFF9C4 !important; /* Açık Sarı */
    }
    
    /* 2. Tüm Yazıları SİYAH Yap */
    h1, h2, h3, h4, h5, h6, p, div, span, label, li, .stMarkdown {
        color: #000000 !important;
    }
    
    /* 3. Buton Tasarımı (Turuncu/Sarı tonlu, Siyah Yazılı) */
    .stButton>button { 
        width: 100%; 
        border-radius: 10px; 
        min-height: 4em; 
        font-weight: 600; 
        background-color: #FFEB3B !important; /* Canlı Sarı */
        color: #000000 !important; 
        border: 2px solid #FBC02D !important; /* Koyu Sarı Kenarlık */
        white-space: pre-wrap; 
        text-align: left !important; 
        padding-left: 20px;
    }
    .stButton>button:hover { 
        background-color: #FDD835 !important; 
        border-color: #000000 !important; 
    }
    
    /* 4. Giriş Kutuları */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important; 
        color: #000000 !important; 
        border: 2px solid #000000 !important;
    }
    
    /* 5. Soru Yazısı Stili */
    .big-font { 
        font-size: 22px !important; 
        font-weight: 800; 
        color: #000000 !important; 
        margin-bottom: 25px; 
    }
    </style>
""", unsafe_allow_html=True)

# --- 1. MÜFREDAT LİSTESİ ---
MUFREDAT = {
    "9. Sınıf": ["Temel Muhasebe", "Mesleki Matematik", "Ofis Uygulamaları", "Mesleki Gelişim Atölyesi"],
    "10. Sınıf": ["Genel Muhasebe", "Temel Hukuk", "Ekonomi", "Klavye Teknikleri"],
    "11. Sınıf": [
        "Bilgisayarlı Muhasebe (Luca)", 
        "Maliyet Muhasebesi", 
        "Şirketler Muhasebesi", 
        "Vergi ve Beyannameler", 
        "İş ve Sosyal Güvenlik Hukuku", 
        "Girişimcilik ve İşletme"
    ],
    "12. Sınıf": [
        "Dış Ticaret", 
        "Kooperatifçilik", 
        "Hızlı Klavye", 
        "Ahilik Kültürü ve Girişimcilik"
    ]
}

# --- 2. DETAYLI KONU HAVUZU (10. SINIF GÜNCELLENDİ) ---
KONU_HAVUZU = {
    # --- 10. SINIF (SİZİN BELİRLEDİĞİNİZ KONULAR) ---
    "Temel Hukuk": [
        "Hukuğa Giriş ve Hukukun Dalları", 
        "Borçlar Hukuku (Borcun Unsurları)", 
        "Hukuki Ehliyet (Hak ve Fiil Ehliyeti)", 
        "Mülkiyet Kavramı ve Hakkı", 
        "Sözleşme Çeşitleri ve Geçersizliği", 
        "Ticaret Hukuku (Tacir, Ticari İşletme)", 
        "Kıymetli Evrak Hukuku (Bono, Poliçe, Çek)", 
        "Sigorta Hukuku (Can ve Mal Sigortası)"
    ],
    "Ekonomi": [
        "Ekonomiye Giriş ve Temel Kavramlar (İhtiyaç, Fayda)", 
        "Arz ve Talep İlişkisi", 
        "Fiyat Oluşumu ve Piyasa Dengesi", 
        "Piyasa Mekanizması (Tam ve Eksik Rekabet)", 
        "Ekonomik Büyüme ve İstihdam", 
        "Para, Bankacılık ve Enflasyon", 
        "Ödemeler Dengesi (Cari Açık/Fazla)", 
        "Dış Ticaret ve Uluslararası Kuruluşlar (IMF, DB, AB)"
    ],
    "Genel Muhasebe": [
        "Bilanço Eşitliği ve Düzenlenmesi", 
        "Muhasebenin Temel Kavramları", 
        "Tekdüzen Hesap Planı Mantığı", 
        "Gelir Tablosu İlkeleri", 
        "Hesapların İşleyişi (Borç/Alacak Kuralları)", 
        "Satılan Ticari Mallar Maliyeti (STMM)", 
        "Muhasebe Uygulamaları (Yevmiye Kayıtları)", 
        "Aktif ve Pasif Hesapların Özellikleri"
    ],
    
    # --- 9. SINIF (ÖNCEKİ YILLIK PLANDAN) ---
    "Temel Muhasebe": ["Ticari Defterler", "Fatura ve İrsaliye", "Perakende Satış Fişi", "Gider Pusulası", "İşletme Hesabı Defteri", "Vergi Dairesi İşlemleri"],
    "Mesleki Matematik": ["Yüzde Hesapları", "Maliyet ve Satış Fiyatı", "KDV Hesaplamaları", "İskonto İşlemleri", "Karışım Problemleri"],
    "Ofis Uygulamaları": ["Word Biçimlendirme", "Excel Formülleri (Topla, Ortalama)", "PowerPoint Sunu Tasarımı", "Yazıcı Ayarları"],
    "Mesleki Gelişim Atölyesi": ["Ahilik Kültürü", "Etkili İletişim", "İş Sağlığı ve Güvenliği", "Girişimcilik Fikirleri"],

    # --- 11. SINIF (ÖNCEKİ YILLIK PLANDAN) ---
    "Bilgisayarlı Muhasebe (Luca)": ["Şirket Açma", "Stok/Cari Kart", "Fatura İşleme", "Muhasebe Fişleri", "KDV Beyannamesi", "Dönem Sonu"],
    "Maliyet Muhasebesi": ["7A/7B Maliyet", "Direkt İlk Madde (150)", "Direkt İşçilik (720)", "Genel Üretim Gideri (730)", "Satılan Mamul Maliyeti"],
    "Şirketler Muhasebesi": ["Şirket Kuruluşu", "Sermaye Artırımı", "Kar Dağıtımı", "Tasfiye", "Şirket Birleşmeleri"],
    "Vergi ve Beyannameler": ["Gelir Vergisi", "Kurumlar Vergisi", "KDV", "MTV", "ÖTV", "Muhtasar Beyanname"],

    # --- 12. SINIF (ÖNCEKİ YILLIK PLANDAN) ---
    "Dış Ticaret": ["İhracat/İthalat Rejimi", "Teslim Şekilleri (Incoterms)", "Ödeme Şekilleri", "Gümrük Mevzuatı"],
    "Kooperatifçilik": ["Kooperatif Kuruluşu", "Ortaklık Hakları", "Risturn Hesaplama", "Genel Kurul"],
    "Hızlı Klavye": ["F Klavye Hız Çalışmaları", "Adli Metin Yazımı", "Rapor Düzenleme"]
}

# --- YEDEK DEPO (ACİL DURUM İÇİN) ---
YEDEK_DEPO = {
    "Genel": [
        {"soru": "VUK'a göre fatura düzenleme sınırı aşıldığında hangi belge düzenlenmelidir?", "secenekler": ["Fatura", "Fiş", "Gider Pusulası", "İrsaliye", "Dekont"], "cevap": "Fatura"},
        {"soru": "Bilanço temel denkliği hangisidir?", "secenekler": ["Varlıklar = Kaynaklar", "Gelir = Gider", "Borç = Alacak", "Aktif = Pasif + Sermaye", "Kasa = Banka"], "cevap": "Varlıklar = Kaynaklar"},
        {"soru": "Excel'de 'EĞER' formülü ne işe yarar?", "secenekler": ["Mantıksal kıyaslama yapar", "Toplama yapar", "Ortalama alır", "Yazı rengini değiştirir", "Tablo çizer"], "cevap": "Mantıksal kıyaslama yapar"}
    ]
}

# --- AI AYARLARI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def yapay_zeka_soru_uret(sinif, ders):
    ai_sorulari = []
    
    # 1. KONU SEÇİMİ (TEKRARI ÖNLEMEK İÇİN)
    # Havuzdan rastgele 3 konu seçiyoruz. Böylece her sınavda farklı konu kombinasyonu gelir.
    tum_konular = KONU_HAVUZU.get(ders, ["Genel Konular"])
    secilen_konular = random.sample(tum_konular, min(3, len(tum_konular)))
    konu_metni = ", ".join(secilen_konular)
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Rolün: Lise Öğretmeni.
        Ders: {ders} (Sınıf: {sinif}).
        
        Aşağıdaki Konulardan 10 ADET özgün test sorusu hazırla:
        KONULAR: {konu_metni}
        
        KURALLAR:
        1. Sorular {sinif} seviyesine uygun ve MEB müfredatıyla uyumlu olsun.
        2. Her sorunun 5 şıkkı (A,B,C,D,E) olsun.
        3. Cevaplar şıklara rastgele dağılsın (Hepsi A olmasın).
        4. Sorular asla tekrar etmemeli, farklı soru tipleri kullan.
        5. Çıktı SADECE JSON formatında olsun.
        
        JSON FORMATI:
        [ {{ "soru": "Soru metni...", "secenekler": ["Şık1", "Şık2", "Şık3", "Şık4", "Şık5"], "cevap": "Doğru şıkkın tam metni" }} ]
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

    # 2. YEDEKLEME (Eksik gelirse)
    if len(ai_sorulari) < 10:
        yedek = YEDEK_DEPO["Genel"]
        eksik = 10 - len(ai_sorulari)
        ai_sorulari.extend(random.choices(yedek, k=eksik))
            
    # 3. KARIŞTIRMA (PYTHON TARAFINDA GARANTİ KARIŞTIRMA)
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

# GİRİŞ EKRANI
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
            
            if not sorular: 
                sorular = YEDEK_DEPO["Genel"]
                
            st.session_state.soru_listesi = sorular
            st.session_state.oturum_basladi = True
            st.session_state.yukleniyor = False
            st.rerun()

# SORU EKRANI
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
            time.sleep(1.5)
            st.session_state.index += 1
            st.rerun()

# SONUÇ EKRANI
else:
    st.balloons()
    st.success("Sınav Tamamlandı!")
    
    st.markdown(f"""
    <div style='background-color:#FFEB3B; padding:20px; border-radius:10px; text-align:center; border: 2px solid #000;'>
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
