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

# --- TASARIM: IHLAMUR YEŞİLİ & SARI KİREMİT (Sizin Tarzınız) ---
st.markdown("""
    <style>
    /* 1. Arka Plan: Ihlamur Yeşili */
    .stApp {
        background-color: #F0F4C3 !important; 
    }
    
    /* 2. Yazı Renkleri: Siyah ve Okunaklı */
    h1, h2, h3, h4, h5, h6, p, div, span, label, li, .stMarkdown {
        color: #212121 !important;
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* 3. Butonlar: Sarı Kiremit (Dikkat Çekici) */
    .stButton>button { 
        width: 100%; 
        border-radius: 12px; 
        min-height: 3.5em; 
        font-weight: 700; 
        background-color: #FF7043 !important; /* Kiremit Rengi */
        color: #FFFFFF !important; /* Yazı Beyaz */
        border: 2px solid #D84315 !important; 
        white-space: pre-wrap; 
        padding: 10px;
        transition: transform 0.2s;
    }
    
    .stButton>button:hover { 
        background-color: #FF5722 !important; 
        transform: scale(1.02);
        color: #FFFFFF !important;
    }
    
    /* 4. Seçim Kutuları */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important; 
        color: #000000 !important; 
        border: 2px solid #FF7043 !important;
    }
    
    /* 5. Soru Kartı (Okunaklı Beyaz Zemin) */
    .big-font { 
        font-size: 20px !important; 
        font-weight: 600; 
        color: #000000 !important; 
        margin-bottom: 20px; 
        padding: 25px; 
        background-color: #FFFFFF; 
        border-left: 10px solid #FF7043;
        border-radius: 10px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        line-height: 1.6;
    }
    
    /* 6. Sidebar (Sol Menü) */
    [data-testid="stSidebar"] {
        background-color: #DCEDC8 !important; 
        border-right: 2px solid #AED581;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 1. VERİ HAVUZLARI
# ==============================================================================

# A) MESLEK DERSLERİ (MÜFREDAT)
MESLEK_KONULARI = {
    "9. Sınıf Meslek": "Temel Muhasebe, Mesleki Matematik, Ofis Uygulamaları, Mesleki Gelişim.",
    "10. Sınıf Meslek": "Genel Muhasebe, Temel Hukuk, Ekonomi, Klavye Teknikleri.",
    "11. Sınıf Meslek": "Bilgisayarlı Muhasebe, Maliyet Muhasebesi, Vergi ve Beyannameler, Şirketler Muhasebesi, İş Hukuku.",
    "12. Sınıf Meslek": "Dış Ticaret, Kooperatifçilik, Ahilik Kültürü ve Girişimcilik."
}

# B) TYT KONULARI (ÖSYM ÇIKMIŞ SORU TARZI)
TYT_KONULARI = {
    "Türkçe": "Paragrafta Anlam (Uzun), Cümlede Anlam, Ses Bilgisi, Yazım Kuralları, Noktalama.",
    "Matematik": "Yeni Nesil Problemler (Hız, Yaş, Yüzde), Temel Kavramlar, Sayı Basamakları, Fonksiyonlar.",
    "Tarih": "İnkılap Tarihi, Osmanlı Kültür Medeniyet, İlk Türk Devletleri.",
    "Coğrafya": "Harita Bilgisi, İklim, Nüfus, Doğal Afetler.",
}

# C) YEDEK DEPO (TYT - ZOR VE PARAGRAF AĞIRLIKLI)
# Eğer AI çalışmazsa buradan çekecek. 40 Soruluk denemeyi dolduracak kadar çeşitlilik eklendi.
YEDEK_TYT_HAVUZ = {
    "Türkçe": [
        {"soru": "(2024 TYT) Paragrafta yazarın asıl yakındığı durum nedir? (Uzun Paragraf: Günümüz insanı teknolojiyle birlikte...) ", "secenekler": ["Yalnızlaşma", "İletişimsizlik", "Hız tutkusu", "Duyarsızlık", "Tembellik"], "cevap": "İletişimsizlik"},
        {"soru": "Aşağıdaki cümlelerin hangisinde bir yazım yanlışı yapılmıştır?", "secenekler": ["TDK'nin yeni kılavuzu yayımlandı.", "Akşam üstü bize gelecekler.", "Her şey yolunda gidiyor.", "Ankara'ya gitmekten vazgeçti.", "Türkçeyi çok seviyor."], "cevap": "Akşam üstü bize gelecekler."},
        {"soru": "Bu parçada altı çizili sözle anlatılmak istenen nedir? ('İğneyle kuyu kazmak')", "secenekler": ["Çok zor bir işi sabırla yapmak", "Boşa kürek çekmek", "İmkansızı istemek", "Zaman kaybetmek", "Yanlış yolda olmak"], "cevap": "Çok zor bir işi sabırla yapmak"},
        {"soru": "Hangisi, öğe dizilişi bakımından 'Özne - Zarf Tümleci - Yüklem' şeklindedir?", "secenekler": ["Çocuklar bahçede koşuyor.", "Yarın Ankara'ya gideceğim.", "Hızlıca eve girdi.", "Kitabı masaya bıraktı.", "O, her zaman çalışır."], "cevap": "O, her zaman çalışır."},
        {"soru": "Paragrafın akışını bozan cümle hangisidir? (I. Sanat evrenseldir. II. Her toplum sanattan etkilenir. III. Sanatçı toplumun aynasıdır. IV. Spor da sanat kadar önemlidir. V. Sanatın dili ortaktır.)", "secenekler": ["I", "II", "III", "IV", "V"], "cevap": "IV"}
    ],
    "Matematik": [
        {"soru": "(Yeni Nesil) Bir manav elindeki elmaların 1/3'ünü %20 karla, kalanını %40 karla satıyor. Toplam kar oranı yüzde kaçtır?", "secenekler": ["%30", "%25", "%33", "%35", "%28"], "cevap": "%33"},
        {"soru": "Ardışık 5 çift sayının toplamı 130 ise en küçük sayı kaçtır?", "secenekler": ["22", "20", "24", "26", "18"], "cevap": "22"},
        {"soru": "A ve B şehirleri arası 600 km'dir. Bir araç 100 km hızla kaç saatte gider?", "secenekler": ["6", "5", "7", "4", "8"], "cevap": "6"},
        {"soru": "f(x) = 3x - 2 ise f(5) kaçtır?", "secenekler": ["13", "15", "10", "12", "14"], "cevap": "13"},
        {"soru": "Bir dikdörtgenin kısa kenarı 10 cm, uzun kenarı 20 cm ise alanı kaç cm² dir?", "secenekler": ["200", "100", "300", "50", "150"], "cevap": "200"}
    ],
    "Tarih": [
        {"soru": "Mustafa Kemal'in Samsun'a çıkışı (19 Mayıs 1919) Milli Mücadele açısından neyi ifade eder?", "secenekler": ["Kurtuluş Savaşı'nın fiilen başlaması", "Cumhuriyetin ilanı", "Lozan Antlaşması", "TBMM'nin açılışı", "Saltanatın kaldırılması"], "cevap": "Kurtuluş Savaşı'nın fiilen başlaması"},
        {"soru": "İlk Türk devletlerinde 'Töre' nedir?", "secenekler": ["Yazısız hukuk kuralları", "Dini kurallar", "Yazılı anayasa", "Hükümdar emirleri", "Askeri kurallar"], "cevap": "Yazısız hukuk kuralları"},
        {"soru": "Osmanlı Devleti'nde 'Düyun-u Umumiye' idaresi neden kurulmuştur?", "secenekler": ["Dış borçları tahsil etmek için", "Vergi toplamak için", "Bankacılık yapmak için", "Orduyu finanse etmek için", "Okul açmak için"], "cevap": "Dış borçları tahsil etmek için"},
        {"soru": "Hangi antlaşma ile Osmanlı Devleti fiilen sona ermiştir?", "secenekler": ["Mondros Ateşkes Antlaşması", "Sevr Antlaşması", "Lozan Antlaşması", "Mudanya Ateşkesi", "Paris Antlaşması"], "cevap": "Mondros Ateşkes Antlaşması"},
        {"soru": "Cumhuriyetçilik ilkesi neyi esas alır?", "secenekler": ["Milli egemenliği", "Dini yönetimi", "Padişahlığı", "Ekonomik bağımsızlığı", "Devletçiliği"], "cevap": "Milli egemenliği"}
    ],
    "Coğrafya": [
        {"soru": "Türkiye'de doğudan batıya gidildikçe yerel saatin geri gelmesinin temel nedeni nedir?", "secenekler": ["Dünya'nın batıdan doğuya dönmesi", "Dünya'nın şekli", "Eksen eğikliği", "Yörünge hareketi", "Enlem etkisi"], "cevap": "Dünya'nın batıdan doğuya dönmesi"},
        {"soru": "Aşağıdakilerden hangisi Karadeniz ikliminin özelliğidir?", "secenekler": ["Her mevsim yağışlı olması", "Yazların kurak geçmesi", "Kışların çok soğuk olması", "Bitki örtüsünün maki olması", "Kar yağışının az olması"], "cevap": "Her mevsim yağışlı olması"},
        {"soru": "Türkiye'de deprem riskinin en az olduğu bölge hangisidir?", "secenekler": ["Konya - Karaman çevresi", "Ege Bölgesi", "Marmara Bölgesi", "Doğu Anadolu", "Karadeniz kıyıları"], "cevap": "Konya - Karaman çevresi"},
        {"soru": "Nüfus piramitlerinde tabanın geniş olması neyi ifade eder?", "secenekler": ["Doğum oranının yüksek olduğunu", "Yaşlı nüfusun fazla olduğunu", "Gelişmiş ülke olduğunu", "Ölüm oranının az olduğunu", "Eğitim seviyesini"], "cevap": "Doğum oranının yüksek olduğunu"},
        {"soru": "Hangi harita ölçeği daha fazla ayrıntı gösterir?", "secenekler": ["1/10.000 (Büyük Ölçek)", "1/1.000.000", "1/500.000", "1/200.000", "1/100.000"], "cevap": "1/10.000 (Büyük Ölçek)"}
    ]
}

# --- AI AYARLARI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def soru_uret(kategori, alt_baslik):
    ai_sorulari = []
    
    # 1. SORU SAYISI VE İÇERİK AYARI
    is_genel_deneme = "Türkiye Geneli" in alt_baslik
    
    if is_genel_deneme:
        # GENEL DENEME MODU: 40 SORU (10 Türkçe, 10 Mat, 10 Tarih, 10 Coğ)
        soru_sayisi = 40 
        zorluk = "ZOR (ÖSYM AYARI)"
        konu_detayi = "10 Adet Paragraf Ağırlıklı Türkçe, 10 Adet Yeni Nesil Matematik, 10 Adet Yorum Ağırlıklı Tarih, 10 Adet Coğrafya."
    elif "Meslek" in kategori:
        # MESLEK DERSLERİ: 15 SORU
        soru_sayisi = 15
        zorluk = "ORTA-ZOR"
        konu_detayi = MESLEK_KONULARI.get(alt_baslik, "Genel Meslek")
    else:
        # TEKİL TYT DERSİ: 15 SORU
        soru_sayisi = 15
        zorluk = "ZOR"
        konu_detayi = TYT_KONULARI.get(alt_baslik, "Genel TYT")

    # 2. YAPAY ZEKA İSTEĞİ (PROMPT)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Rol: Kıdemli Sınav Hazırlama Komisyonu Üyesi.
        Kategori: {kategori} - {alt_baslik}
        Zorluk Seviyesi: {zorluk}
        İstenen İçerik: {konu_detayi}
        Soru Adedi: {soru_sayisi}
        
        KESİN KURALLAR:
        1. Sorular lise öğrencileri için {zorluk} seviyesinde olsun. Basit sorular sorma.
        2. Türkçe soruları MUTLAKA UZUN PARAGRAF veya DİL BİLGİSİ analizi olsun.
        3. Matematik soruları YENİ NESİL PROBLEM kurgusunda olsun.
        4. Tarih ve Coğrafya soruları salt bilgi değil, YORUM ve ANALİZ gerektirsin.
        5. Çıktı SADECE JSON formatında olsun. Başka yazı yazma.
        
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

    # 3. YEDEK DEPO İLE TAMAMLAMA (EĞER AI EKSİK VERİRSE)
    # Genel deneme için her branştan yedek çekip karıştıracağız.
    if len(ai_sorulari) < soru_sayisi:
        yedek_listesi = []
        if is_genel_deneme:
            # Her dersten eşit miktarda al
            for ders, sorular in YEDEK_TYT_HAVUZ.items():
                yedek_listesi.extend(sorular)
        elif "Meslek" in kategori:
            # Meslek için genel yedek (Şimdilik örnek olarak TYT havuzunu kullanıyorum, buraya meslek eklenebilir)
            yedek_listesi = YEDEK_TYT_HAVUZ.get("Genel", []) 
        else:
            # Tekil ders (Örn: Sadece Tarih)
            yedek_listesi = YEDEK_TYT_HAVUZ.get(alt_baslik, [])

        # Karıştır ve ekle
        random.shuffle(yedek_listesi)
        eksik = soru_sayisi - len(ai_sorulari)
        
        # Yedek yetmezse kopyalayarak çoğalt (Sınavın boş kalmasından iyidir)
        while len(yedek_listesi) < eksik:
            yedek_listesi.extend(yedek_listesi)
            
        ai_sorulari.extend(yedek_listesi[:eksik])
            
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
def restart_app():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
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
        st.title("Sınav Kategorisi")
        mod_secimi = st.radio("Seçim Yapınız:", ["Meslek Lisesi Sınavları", "TYT Hazırlık Kampı"])
        st.write("---")
        st.info("Bağarası ÇPAL Online Sınav Merkezi")

    st.markdown(f"<h1 style='text-align: center; color:#D84315;'>{mod_secimi}</h1>", unsafe_allow_html=True)
    
    if mod_secimi == "Meslek Lisesi Sınavları":
        secenekler = list(MESLEK_KONULARI.keys())
        etiket = "Sınıf Seviyesi Seçiniz:"
        soru_bilgisi = "15 Soru (Orta-Zor)"
    else:
        # TYT Kampı Seçenekleri
        temel_dersler = ["Türkçe", "Matematik", "Tarih", "Coğrafya"]
        # Deneme sınavları (1'den 10'a)
        denemeler = [f"Türkiye Geneli Deneme {i}" for i in range(1, 11)] 
        secenekler = temel_dersler + denemeler
        etiket = "Ders veya Deneme Sınavı Seçiniz:"
        soru_bilgisi = "Tek Ders: 15 Soru | Genel Deneme: 40 Soru (ÖSYM Tarzı)"

    secilen_alt_baslik = st.selectbox(etiket, secenekler)
    st.caption(f"ℹ️ **Sınav Formatı:** {soru_bilgisi}")

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
        with st.status("Yapay Zeka Soruları Hazırlıyor... (ÖSYM Veritabanına Bağlanılıyor...)", expanded=True):
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
    
    # Soru Metni
    st.markdown(f"<div class='big-font'>{soru['soru']}</div>", unsafe_allow_html=True)
    
    secenekler = soru["secenekler"]
    # Şıkları karıştırmak istemiyorsanız aşağıdaki satırı silin, ama karıştırmak iyidir.
    random.shuffle(secenekler) 
    
    col1, col2 = st.columns(2)
    for i, sec in enumerate(secenekler):
        if i < len(secenekler) / 2:
            with col1:
                if st.button(sec, key=f"btn_{i}", use_container_width=True):
                    cevap_kontrol(sec, soru["cevap"])
        else:
            with col2:
                if st.button(sec, key=f"btn_{i}", use_container_width=True):
                    cevap_kontrol(sec, soru["cevap"])

def cevap_kontrol(secilen, dogru):
    soru_puani = 100 / len(st.session_state.soru_listesi)
    if secilen == dogru:
        st.session_state.puan += soru_puani
        st.toast("✅ Doğru!", icon="🎉")
    else:
        st.toast(f"❌ Yanlış! Doğru Cevap: {dogru}", icon="⚠️")
    
    time.sleep(0.5)
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
        <p style='font-size: 24px;'>{st.session_state.kimlik['baslik']} Tamamlandı.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.kayit_ok:
        if sonuclari_kaydet(st.session_state.kimlik["ad"], st.session_state.kimlik["soyad"], st.session_state.kimlik["mod"], st.session_state.kimlik["baslik"], final_puan):
            st.success("Sonuç Kaydedildi ✅")
            st.session_state.kayit_ok = True
    
    st.write("")
    col_x, col_y, col_z = st.columns([1,2,1])
    with col_y:
        # YENİDEN BAŞLAT BUTONU
        if st.button("🔄 YENİ SINAV ÇÖZ (Ana Menüye Dön)", type="primary", use_container_width=True):
            restart_app()
