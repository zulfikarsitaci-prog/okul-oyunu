import streamlit as st
import google.generativeai as genai
import json
import time
import random
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Bağarası Hibrit Eğitim Merkezi", page_icon="🎓", layout="wide")

# --- TASARIM: IHLAMUR YEŞİLİ & SARI KİREMİT ---
st.markdown("""
    <style>
    .stApp { background-color: #F0F4C3 !important; }
    h1, h2, h3, h4, h5, h6, p, div, span, label, li, .stMarkdown { color: #212121 !important; font-family: 'Segoe UI', sans-serif; }
    .stButton>button { 
        width: 100%; border-radius: 12px; min-height: 3.5em; font-weight: 700; 
        background-color: #FF7043 !important; color: #FFFFFF !important; 
        border: 2px solid #D84315 !important; transition: transform 0.2s;
    }
    .stButton>button:hover { background-color: #FF5722 !important; transform: scale(1.02); }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important; color: #000000 !important; border: 2px solid #FF7043 !important;
    }
    .big-font { 
        font-size: 20px !important; font-weight: 600; color: #000000 !important; 
        margin-bottom: 20px; padding: 20px; background-color: rgba(255,255,255,0.8); 
        border-left: 8px solid #FF7043; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    [data-testid="stSidebar"] { background-color: #DCEDC8 !important; border-right: 2px solid #AED581; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 1. VERİ VE KONU HAVUZLARI
# ==============================================================================

# MESLEK DERSLERİ KONULARI (Yıllık Planlardan)
MESLEK_KONULARI = {
    "9. Sınıf Meslek": "Temel Muhasebe (Fatura, Defterler), Mesleki Matematik (Yüzde, Kar/Zarar), Ofis (Word, Excel), Ahilik Kültürü.",
    "10. Sınıf Meslek": "Genel Muhasebe (Bilanço, Yevmiye), Hukuk (Hak, Borç), Ekonomi (Arz-Talep), Klavye (F Klavye).",
    "11. Sınıf Meslek": "Bilgisayarlı Muhasebe (Fişler), Maliyet (7A/7B), Vergi (Beyannameler), Şirketler, İş Hukuku.",
    "12. Sınıf Meslek": "Dış Ticaret (İhracat/İthalat), Kooperatifçilik, Ahilik ve Girişimcilik."
}

# TYT KONU DAĞILIMI (ÖSYM Çıkmış Soru Tarzı)
TYT_KONULARI = {
    "Türkçe": "Paragrafta Anlam (Uzun), Cümlede Anlam, Ses Bilgisi, Yazım Kuralları, Noktalama.",
    "Matematik": "Yeni Nesil Problemler, Temel Kavramlar, Sayı Basamakları, Fonksiyonlar.",
    "Tarih": "İnkılap Tarihi, Osmanlı Kültür Medeniyet, İlk Türk Devletleri.",
    "Coğrafya": "Harita Bilgisi, İklim, Nüfus, Doğal Afetler.",
    "Deneme": "Türkçe (Paragraf ağırlıklı), Matematik (Problem ağırlıklı), Tarih, Coğrafya karma."
}

# YEDEK DEPO (SİSTEM ÇÖKERSE DEVREYE GİRER - TYT ÇIKMIŞ BENZERİ)
YEDEK_TYT_HAVUZ = [
    {"soru": "(2023 TYT Benzeri) Paragrafta anlatılmak istenen asıl düşünce nedir? (Uzun paragraf varsayımı...)", "secenekler": ["İletişimin önemi", "Empatinin gücü", "Sanatın topluma etkisi", "Bilimin ilerlemesi", "Tarihin tekerrürü"], "cevap": "Sanatın topluma etkisi"},
    {"soru": "(2022 TYT Benzeri) Bir manavın elindeki elmaların 1/3'ü çürümüştür. Kalanların yarısı satılmıştır. Geriye 10 kg elma kaldığına göre başlangıçta kaç kg elma vardır?", "secenekler": ["30", "40", "60", "20", "50"], "cevap": "30"},
    {"soru": "(2021 TYT Benzeri) Aşağıdaki cümlelerin hangisinde yazım yanlışı vardır?", "secenekler": ["Herşey güzel olacak.", "Akşam bize geldi.", "Türkçe dersini seviyorum.", "Ankara'ya gittik.", "Kitap okumayı severim."], "cevap": "Herşey güzel olacak."},
    {"soru": "(2020 TYT Benzeri) Mustafa Kemal'in Samsun'a çıkışı hangi amaca yöneliktir?", "secenekler": ["Milli Mücadeleyi başlatmak", "İstanbul'a dönmek", "Tatile gitmek", "Arkadaşlarıyla buluşmak", "Ticaret yapmak"], "cevap": "Milli Mücadeleyi başlatmak"},
    {"soru": "(2019 TYT Benzeri) Türkiye'de en çok yağış alan bölge hangisidir?", "secenekler": ["Karadeniz", "Akdeniz", "Ege", "İç Anadolu", "Güneydoğu"], "cevap": "Karadeniz"},
    # ... (Burası normalde yüzlerce soruyla dolu olmalı, örnek olarak kısa tuttum)
]

# --- AI AYARLARI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def soru_uret(kategori, alt_baslik):
    ai_sorulari = []
    
    # 1. SORU SAYISI VE ZORLUK AYARI
    if "Türkiye Geneli" in alt_baslik:
        soru_sayisi = 40 # Denemeler 40 soru
        zorluk = "ZOR (ÖSYM AYARI)"
        konu_detayi = "Türkçe (20 Soru Paragraf), Matematik (10 Soru Problem), Tarih (5 Soru), Coğrafya (5 Soru)"
    elif "Meslek" in kategori:
        soru_sayisi = 15
        zorluk = "ORTA-ZOR"
        konu_detayi = MESLEK_KONULARI.get(alt_baslik, "Genel Meslek")
    else:
        soru_sayisi = 15
        zorluk = "ORTA"
        konu_detayi = TYT_KONULARI.get(alt_baslik, "Genel TYT")

    # 2. YAPAY ZEKA İSTEĞİ (PROMPT)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Rol: ÖSYM Soru Hazırlama Uzmanı ve Meslek Dersi Öğretmeni.
        Kategori: {kategori} - {alt_baslik}
        Zorluk Seviyesi: {zorluk}
        İstenen İçerik: {konu_detayi}
        Soru Adedi: {soru_sayisi}
        
        ÖZEL KURALLAR:
        1. Sorular kesinlikle 'Aşağıdakilerden hangisi' tarzı basit sorular olmasın.
        2. Türkçe soruları UZUN PARAGRAF olsun.
        3. Matematik soruları YENİ NESİL PROBLEM olsun.
        4. Tarih ve Coğrafya soruları YORUM ağırlıklı olsun.
        5. Eğer "Türkiye Geneli Deneme" ise, sorular son 5 yılın (2019-2024) çıkmış sorularına çok benzer olsun.
        6. Çıktı SADECE JSON formatında olsun.
        
        JSON FORMATI:
        [ {{ "soru": "Uzun soru metni...", "secenekler": ["A", "B", "C", "D", "E"], "cevap": "Doğru şıkkın tam metni" }} ]
        """
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"): text = text.split("```")[1].strip()
        if text.startswith("json"): text = text[4:].strip()
        ai_sorulari = json.loads(text)
    except:
        ai_sorulari = []

    # 3. YEDEK DEPO (EKSİK VARSA TAMAMLA)
    if len(ai_sorulari) < soru_sayisi:
        yedek = YEDEK_TYT_HAVUZ # Şimdilik genel havuzdan çekiyor, buraya binlerce soru eklenebilir.
        eksik = soru_sayisi - len(ai_sorulari)
        # Karıştır ve ekle
        random.shuffle(yedek)
        import copy
        yedek_kopya = copy.deepcopy(yedek)
        while len(yedek_kopya) < eksik: yedek_kopya.extend(yedek_kopya) # Yetmezse çoğalt
        ai_sorulari.extend(yedek_kopya[:eksik])
            
    return ai_sorulari[:soru_sayisi]

# --- KAYIT SİSTEMİ ---
def sonuclari_kaydet(ad, soyad, kategori, alt_baslik, puan):
    try:
        if "gcp_service_account" in st.secrets:
            secrets_dict = st.secrets["gcp_service_account"]
            scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_info(secrets_dict, scopes=scope)
            client = gspread.authorize(creds)
            sheet = client.open("Okul_Puanlari").sheet1
            tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
            sheet.append_row([tarih, f"{ad} {soyad}", kategori, alt_baslik, puan])
            return True
        return False
    except:
        return False

# --- UYGULAMA RESETLEME (YENİ SINAV İÇİN) ---
def reset_app():
    st.session_state.oturum_basladi = False
    st.session_state.soru_listesi = []
    st.session_state.index = 0
    st.session_state.puan = 0
    st.session_state.kayit_ok = False
    st.session_state.yukleniyor = False
    st.rerun()

# --- EKRAN AKIŞI (SESSION STATE) ---
if 'oturum_basladi' not in st.session_state: st.session_state.oturum_basladi = False
if 'soru_listesi' not in st.session_state: st.session_state.soru_listesi = []
if 'index' not in st.session_state: st.session_state.index = 0
if 'puan' not in st.session_state: st.session_state.puan = 0
if 'yukleniyor' not in st.session_state: st.session_state.yukleniyor = False
if 'kayit_ok' not in st.session_state: st.session_state.kayit_ok = False

# GİRİŞ EKRANI
if not st.session_state.oturum_basladi:
    # Sidebar
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2997/2997321.png", width=120)
        st.title("Sınav Modu Seçin")
        mod_secimi = st.radio("Kategori:", ["Meslek Lisesi Sınavları", "TYT Hazırlık Kampı"])
        st.write("---")
        st.info("💡 **İpucu:** Türkiye Geneli Denemeler, gerçek sınav provası niteliğindedir.")

    st.markdown(f"<h1 style='text-align: center; color:#D84315;'>{mod_secimi}</h1>", unsafe_allow_html=True)
    
    if mod_secimi == "Meslek Lisesi Sınavları":
        secenekler = list(MESLEK_KONULARI.keys())
        etiket = "Sınıf Seviyesi Seçiniz:"
        st.info("Bu modda seçtiğiniz sınıfın **TÜM MESLEK DERSLERİNDEN** karışık 15 soru gelir.")
    else:
        # TYT Kampı Seçenekleri
        temel_dersler = ["Türkçe", "Matematik", "Tarih", "Coğrafya"]
        denemeler = [f"Türkiye Geneli Deneme {i}" for i in range(1, 11)] # 1'den 10'a kadar deneme
        secenekler = temel_dersler + denemeler
        etiket = "Ders veya Deneme Sınavı Seçiniz:"
        st.warning("⚠️ **Türkiye Geneli Denemeler 40 Sorudan oluşur ve Zordur.**")

    secilen_alt_baslik = st.selectbox(etiket, secenekler)

    with st.form("giris"):
        c1, c2 = st.columns(2)
        ad = c1.text_input("Adınız")
        soyad = c2.text_input("Soyadınız")
        if st.form_submit_button("SINAVI BAŞLAT 🚀"):
            if ad and soyad:
                st.session_state.kimlik = {"ad": ad, "soyad": soyad, "mod": mod_secimi, "baslik": secilen_alt_baslik}
                st.session_state.yukleniyor = True
                st.rerun()

    if st.session_state.yukleniyor:
        with st.status("Yapay Zeka Soruları Hazırlıyor... (Lütfen Bekleyiniz)", expanded=True):
            sorular = soru_uret(st.session_state.kimlik['mod'], st.session_state.kimlik['baslik'])
            st.session_state.soru_listesi = sorular
            st.session_state.oturum_basladi = True
            st.session_state.yukleniyor = False
            st.rerun()

# SORU EKRANI
elif st.session_state.index < len(st.session_state.soru_listesi):
    soru = st.session_state.soru_listesi[st.session_state.index]
    toplam = len(st.session_state.soru_listesi)
    
    # İlerleme Çubuğu ve Başlık
    st.progress((st.session_state.index + 1) / toplam)
    st.markdown(f"**{st.session_state.kimlik['baslik']}** | Soru {st.session_state.index + 1} / {toplam}")
    
    # Soru Metni (Zor sorular için büyük alan)
    st.markdown(f"<div class='big-font'>{soru['soru']}</div>", unsafe_allow_html=True)
    
    secenekler = soru["secenekler"]
    random.shuffle(secenekler) # Şıkları karıştır
    
    col1, col2 = st.columns(2) # Şıkları 2 sütuna böl (daha şık durur)
    for i, sec in enumerate(secenekler):
        # İlk yarısı sol sütuna, kalanı sağ sütuna
        if i < len(secenekler) / 2:
            with col1:
                if st.button(sec, key=f"btn_{i}", use_container_width=True):
                    cevap_kontrol(sec, soru["cevap"])
        else:
            with col2:
                if st.button(sec, key=f"btn_{i}", use_container_width=True):
                    cevap_kontrol(sec, soru["cevap"])

def cevap_kontrol(secilen, dogru):
    # Puanlama: Toplam 100 puan üzerinden soru başına puan
    soru_puani = 100 / len(st.session_state.soru_listesi)
    
    if secilen == dogru:
        st.session_state.puan += soru_puani
        st.toast("✅ Doğru Cevap!", icon="🎉")
    else:
        st.toast(f"❌ Yanlış! Doğru Cevap: {dogru}", icon="⚠️")
    
    time.sleep(0.8) # Hızlı geçiş
    st.session_state.index += 1
    st.rerun()

# SONUÇ EKRANI
else:
    st.balloons()
    final_puan = int(st.session_state.puan)
    
    st.markdown(f"""
    <div style='background-color:#FF7043; padding:40px; border-radius:20px; text-align:center; color:white; box-shadow: 0 10px 30px rgba(0,0,0,0.3);'>
        <h2 style='color:white;'>Tebrikler {st.session_state.kimlik['ad']}!</h2>
        <h1 style='font-size: 80px; margin: 20px 0;'>{final_puan}</h1>
        <p style='font-size: 24px;'>{st.session_state.kimlik['baslik']} Sınavı Tamamlandı.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Otomatik Kayıt
    if not st.session_state.kayit_ok:
        if sonuclari_kaydet(st.session_state.kimlik["ad"], st.session_state.kimlik["soyad"], st.session_state.kimlik["mod"], st.session_state.kimlik["baslik"], final_puan):
            st.success("Sonuçlarınız Öğretmeninize Başarıyla İletildi. ✅")
            st.session_state.kayit_ok = True
    
    st.write("")
    st.write("")
    
    # YENİDEN BAŞLAT BUTONU (Sayfayı yenilemeden başa döner)
    if st.button("🔄 Ana Menüye Dön / Yeni Sınav Çöz", type="primary"):
        reset_app()
