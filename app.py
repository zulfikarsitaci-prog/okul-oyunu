import streamlit as st
import google.generativeai as genai
import json
import time
import random
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Bağarası Hibrit Eğitim Merkezi", page_icon="🎓", layout="centered")

# --- TASARIM: IHLAMUR YEŞİLİ & SARI KİREMİT ---
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
    
    /* 3. Butonlar: Sarı Kiremit / Turuncu Tonları */
    .stButton>button { 
        width: 100%; 
        border-radius: 12px; 
        min-height: 4.5em; 
        font-weight: 700; 
        background-color: #FF7043 !important; /* Kiremit Rengi */
        color: #FFFFFF !important; /* Yazı Beyaz olsun ki okunsun */
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
    
    /* 4. Seçim Kutuları ve Inputlar */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important; 
        color: #000000 !important; 
        border: 2px solid #FF7043 !important;
    }
    
    /* 5. Soru Kartı */
    .big-font { 
        font-size: 22px !important; 
        font-weight: 700; 
        color: #000000 !important; 
        margin-bottom: 25px; 
        padding: 20px; 
        background-color: rgba(255,255,255,0.7); 
        border-left: 8px solid #FF7043;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* 6. Sidebar (Sol Menü) */
    [data-testid="stSidebar"] {
        background-color: #DCEDC8 !important; /* Daha koyu ıhlamur */
        border-right: 2px solid #AED581;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 1. VERİ HAVUZLARI (MÜFREDAT VE TYT)
# ==============================================================================

# A) MESLEK DERSLERİ GRUPLAMASI (Sınıflara Göre Karışık)
MESLEK_GRUPLARI = {
    "9. Sınıf Meslek": [
        "Temel Muhasebe (Fatura, Defterler)", 
        "Mesleki Matematik (Yüzde, Maliyet, KDV)", 
        "Ofis Uygulamaları (Word, Excel, PowerPoint)", 
        "Mesleki Gelişim (Ahilik, İletişim)"
    ],
    "10. Sınıf Meslek": [
        "Genel Muhasebe (Bilanço, Yevmiye, Mizan)", 
        "Temel Hukuk (Hak, Borç, Sözleşme)", 
        "Ekonomi (Arz-Talep, Enflasyon)", 
        "Klavye Teknikleri (F Klavye)"
    ],
    "11. Sınıf Meslek": [
        "Bilgisayarlı Muhasebe (Luca/ETA, Fişler)", 
        "Maliyet Muhasebesi (7A/7B, Üretim Maliyeti)", 
        "Vergi ve Beyannameler (KDV, Muhtasar, Gelir)", 
        "Şirketler Muhasebesi (Kuruluş, Kar Dağıtımı)",
        "İş ve Sosyal Güvenlik Hukuku"
    ],
    "12. Sınıf Meslek": [
        "Dış Ticaret (İhracat, İthalat, Gümrük)", 
        "Kooperatifçilik (Kuruluş, Genel Kurul)", 
        "Ahilik Kültürü ve Girişimcilik"
    ]
}

# B) TYT KONU BAŞLIKLARI (Son 5 Yıl Analizi)
TYT_KONULARI = {
    "Türkçe": "Paragrafta Anlam, Sözcükte Anlam, Ses Bilgisi, Yazım Kuralları, Noktalama İşaretleri, Dil Bilgisi (Öge, Tür).",
    "Matematik": "Temel Kavramlar, Sayı Basamakları, Problemler (Hız, Yaş, Yüzde), Fonksiyonlar, Kümeler, Polinomlar.",
    "Tarih": "İlk Türk Devletleri, Osmanlı Kültür Medeniyet, Kurtuluş Savaşı, Atatürk İlkeleri ve İnkılapları.",
    "Coğrafya": "Doğa ve İnsan, Harita Bilgisi, İklim Bilgisi, Nüfus ve Yerleşme, Doğal Afetler.",
    "Genel Deneme": "Türkçe (Paragraf), Matematik (Problemler), Tarih ve Coğrafya karma sorular."
}

# C) YEDEK DEPO (MESLEK - KARIŞIK)
YEDEK_MESLEK = {
    "9. Sınıf Meslek": [
        {"soru": "Çiftçiden ürün alırken düzenlenen belge hangisidir?", "secenekler": ["Müstahsil Makbuzu", "Fatura", "Gider Pusulası", "İrsaliye", "Fiş"], "cevap": "Müstahsil Makbuzu"},
        {"soru": "KDV hariç 500 TL olan malın %20 KDV tutarı kaçtır?", "secenekler": ["100 TL", "50 TL", "20 TL", "120 TL", "80 TL"], "cevap": "100 TL"},
        {"soru": "Excel'de toplama formülü nedir?", "secenekler": ["=TOPLA()", "=ÇIKAR()", "=SAY()", "=EĞER()", "=ORTALAMA()"], "cevap": "=TOPLA()"},
        {"soru": "Ahiliğin kurucusu kimdir?", "secenekler": ["Ahi Evran", "Mevlana", "Yunus Emre", "Hacı Bektaş", "Kaşgarlı Mahmut"], "cevap": "Ahi Evran"},
        {"soru": "Maliyet fiyatı üzerine kar eklenince ne bulunur?", "secenekler": ["Satış Fiyatı", "Zarar", "Gider", "İskonto", "Ciro"], "cevap": "Satış Fiyatı"}
    ],
    "10. Sınıf Meslek": [
        {"soru": "Bilanço temel denkliği hangisidir?", "secenekler": ["Varlıklar = Kaynaklar", "Gelir = Gider", "Aktif = Pasif - Sermaye", "Kasa = Banka", "Borç = Alacak"], "cevap": "Varlıklar = Kaynaklar"},
        {"soru": "Hak ehliyeti ne zaman başlar?", "secenekler": ["Tam ve sağ doğumla", "18 yaşla", "Evlenince", "Okula başlayınca", "İşe girince"], "cevap": "Tam ve sağ doğumla"},
        {"soru": "Fiyatlar genel seviyesinin sürekli artmasına ne denir?", "secenekler": ["Enflasyon", "Devalüasyon", "Resesyon", "Deflasyon", "Kriz"], "cevap": "Enflasyon"},
        {"soru": "100 Kasa hesabı nasıl çalışır?", "secenekler": ["Girişler Borç, Çıkışlar Alacak", "Girişler Alacak, Çıkışlar Borç", "Hep Alacaklı", "Hep Borçlu", "Çalışmaz"], "cevap": "Girişler Borç, Çıkışlar Alacak"},
        {"soru": "Tacir kime denir?", "secenekler": ["Ticari işletmeyi işleten", "Memur", "İşçi", "Öğrenci", "Emekli"], "cevap": "Ticari işletmeyi işleten"}
    ],
    "11. Sınıf Meslek": [
        {"soru": "KDV beyannamesi ne zaman verilir?", "secenekler": ["Takip eden ayın 28'i", "Yıl sonunda", "Her hafta", "Günlük", "3 ayda bir"], "cevap": "Takip eden ayın 28'i"},
        {"soru": "7/A seçeneğinde Direkt İlk Madde ve Malzeme Giderleri kodu nedir?", "secenekler": ["710", "720", "730", "740", "750"], "cevap": "710"},
        {"soru": "Bilgisayarlı muhasebede 'Fiş Kaydı' nereden yapılır?", "secenekler": ["Muhasebe Modülü", "Stok Modülü", "Cari Modülü", "Çek/Senet", "Fatura"], "cevap": "Muhasebe Modülü"},
        {"soru": "Kıdem tazminatı alabilmek için en az ne kadar çalışmak gerekir?", "secenekler": ["1 Yıl", "6 Ay", "3 Ay", "1 Ay", "5 Yıl"], "cevap": "1 Yıl"},
        {"soru": "Kurumlar Vergisi oranı (2024) yaklaşık kaçtır?", "secenekler": ["%25", "%10", "%50", "%1", "%5"], "cevap": "%25"}
    ],
    "12. Sınıf Meslek": [
        {"soru": "İhracat nedir?", "secenekler": ["Yurt dışına mal satmak", "Yurt dışından mal almak", "Üretim yapmak", "Vergi ödemek", "Depolama"], "cevap": "Yurt dışına mal satmak"},
        {"soru": "Kooperatiflerin temel amacı nedir?", "secenekler": ["Ortakların ekonomik menfaatlerini korumak", "Kar maksimizasyonu", "Rakip firmaları yok etmek", "Vergi vermemek", "Siyaset yapmak"], "cevap": "Ortakların ekonomik menfaatlerini korumak"},
        {"soru": "FOB teslim şekli ne anlama gelir?", "secenekler": ["Gemi güvertesinde teslim", "Fabrikada teslim", "Gümrükte teslim", "Sigorta dahil teslim", "Kapıda ödeme"], "cevap": "Gemi güvertesinde teslim"},
        {"soru": "Ahilikte kalfalıktan ustalığa geçiş törenine ne denir?", "secenekler": ["Şed Kuşanma", "Mezuniyet", "Diploma", "İcazet", "Terfi"], "cevap": "Şed Kuşanma"},
        {"soru": "Gümrük vergisi kime ödenir?", "secenekler": ["Gümrük İdaresine", "Belediyeye", "Satıcıya", "Alıcıya", "Nakliyeciye"], "cevap": "Gümrük İdaresine"}
    ]
}

# D) YEDEK DEPO (TYT - ÇIKMIŞ SORU BENZERLERİ)
YEDEK_TYT = {
    "Türkçe": [
        {"soru": "Paragrafta 'yakınmak' ne anlama gelir?", "secenekler": ["Şikayet etmek", "Beğenmek", "Özlemek", "Kıskanmak", "Sevmek"], "cevap": "Şikayet etmek"},
        {"soru": "Hangi cümlede yazım yanlışı vardır?", "secenekler": ["Herşey çok güzel olacak.", "Bu akşam gelebilirim.", "Türkçe dersini seviyorum.", "Ankara'ya gittim.", "Kitap okumayı severim."], "cevap": "Herşey çok güzel olacak."}
    ],
    "Matematik": [
        {"soru": "Bir sayının 3 katının 5 eksiği 10 ise bu sayı kaçtır?", "secenekler": ["5", "3", "4", "6", "10"], "cevap": "5"},
        {"soru": "Ardışık 3 tek sayının toplamı 33 ise en büyüğü kaçtır?", "secenekler": ["13", "11", "9", "15", "17"], "cevap": "13"}
    ],
    "Tarih": [
        {"soru": "Mustafa Kemal'e 'Atatürk' soyadı hangi kanunla verilmiştir?", "secenekler": ["Soyadı Kanunu", "Teşkilat-ı Esasiye", "Medeni Kanun", "Tevhid-i Tedrisat", "Şapka Kanunu"], "cevap": "Soyadı Kanunu"},
        {"soru": "İlk Türk devletlerinde devlet işlerinin görüşüldüğü meclise ne denir?", "secenekler": ["Kurultay (Toy)", "Divan", "Senato", "Meclis", "Pankuş"], "cevap": "Kurultay (Toy)"}
    ],
    "Coğrafya": [
        {"soru": "Türkiye'de en çok yağış alan bölge hangisidir?", "secenekler": ["Karadeniz", "Akdeniz", "Ege", "İç Anadolu", "Güneydoğu Anadolu"], "cevap": "Karadeniz"},
        {"soru": "Aşağıdakilerden hangisi doğal bir afettir?", "secenekler": ["Deprem", "Trafik kazası", "Savaş", "Göç", "Sanayileşme"], "cevap": "Deprem"}
    ],
    "Genel Deneme": [
        {"soru": "Milli Mücadelenin başlangıcı kabul edilen olay nedir?", "secenekler": ["19 Mayıs 1919 Samsun'a Çıkış", "TBMM'nin Açılışı", "Cumhuriyetin İlanı", "Sivas Kongresi", "Lozan Antlaşması"], "cevap": "19 Mayıs 1919 Samsun'a Çıkış"},
        {"soru": "Bir sınıftaki 20 öğrencinin %40'ı kız ise kaç erkek öğrenci vardır?", "secenekler": ["12", "8", "10", "14", "16"], "cevap": "12"}
    ]
}

# --- AI AYARLARI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def soru_uret(kategori, alt_baslik):
    ai_sorulari = []
    
    # Kategoriye göre konu listesi belirle
    if "Meslek" in kategori:
        # Meslek lisesi ise o sınıfın tüm derslerini birleştir
        konu_listesi = ", ".join(MESLEK_GRUPLARI.get(alt_baslik, []))
        prompt_rol = f"Sen Uzman bir Meslek Lisesi Öğretmenisin. {alt_baslik} seviyesindeki öğrencilere sınav hazırlıyorsun."
        prompt_gorev = f"Şu derslerin HEPSİNDEN KARIŞIK toplam 15 soru hazırla: {konu_listesi}."
        prompt_ek = "Özellikle Bilgisayarlı Muhasebe (ETA/Luca/Fişler), Vergi, Maliyet ve Hukuk konularına ağırlık ver."
    else:
        # TYT ise seçilen dersten sor
        konu_listesi = TYT_KONULARI.get(alt_baslik, "TYT Genel")
        prompt_rol = "Sen ÖSYM formatına hakim bir TYT Uzmanısın."
        prompt_gorev = f"Son 5 yılın TYT sınavlarında çıkmış sorulara benzer, {alt_baslik} dersinden 15 adet özgün soru hazırla."
        prompt_ek = "Sorular yorum, analiz ve bilgi ağırlıklı olsun (Yeni Nesil Sorular)."

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        {prompt_rol}
        {prompt_gorev}
        {prompt_ek}
        
        KURALLAR:
        1. Çıktı SADECE JSON formatında olsun.
        2. Her sorunun 5 şıkkı (A,B,C,D,E) olsun.
        3. Cevaplar rastgele şıklara dağılsın.
        
        JSON FORMATI:
        [ {{ "soru": "...", "secenekler": ["A", "B", "C", "D", "E"], "cevap": "..." }} ]
        """
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        if text_response.startswith("```"): text_response = text_response.split("```")[1].strip()
        if text_response.startswith("json"): text_response = text_response[4:].strip()
        ai_sorulari = json.loads(text_response)
    except:
        ai_sorulari = []

    # EKSİK KALIRSA YEDEKTEN TAMAMLA
    target_count = 15
    if len(ai_sorulari) < target_count:
        if "Meslek" in kategori:
            yedek = YEDEK_MESLEK.get(alt_baslik, YEDEK_MESLEK["9. Sınıf Meslek"])
        else:
            yedek = YEDEK_TYT.get(alt_baslik, YEDEK_TYT["Genel Deneme"])
            
        eksik = target_count - len(ai_sorulari)
        random.shuffle(yedek)
        # Yedek azsa çoğalt
        while len(yedek) < eksik: yedek.extend(yedek)
        ai_sorulari.extend(yedek[:eksik])
            
    return ai_sorulari[:target_count]

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

# --- EKRAN AKIŞI ---
if 'oturum_basladi' not in st.session_state: st.session_state.oturum_basladi = False
if 'soru_listesi' not in st.session_state: st.session_state.soru_listesi = []
if 'index' not in st.session_state: st.session_state.index = 0
if 'puan' not in st.session_state: st.session_state.puan = 0
if 'yukleniyor' not in st.session_state: st.session_state.yukleniyor = False
if 'kayit_ok' not in st.session_state: st.session_state.kayit_ok = False

# GİRİŞ EKRANI
if not st.session_state.oturum_basladi:
    # Sidebar Menü
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2997/2997321.png", width=100)
        st.title("Sınav Modu")
        mod_secimi = st.radio("Bir Bölüm Seçin:", ["Meslek Lisesi Sınavları", "TYT Hazırlık Kampı"])
        st.info("Bağarası ÇPAL Yapay Zeka Destekli Sınav Sistemi")

    st.markdown(f"<h1 style='text-align: center; color:#E65100;'>{mod_secimi}</h1>", unsafe_allow_html=True)
    
    if mod_secimi == "Meslek Lisesi Sınavları":
        secenekler = list(MESLEK_GRUPLARI.keys())
        etiket = "Sınıf Seviyesi Seçiniz:"
    else:
        secenekler = ["Türkçe", "Matematik", "Tarih", "Coğrafya", "Genel Deneme"]
        etiket = "Ders / Deneme Seçiniz:"
        
    secilen_alt_baslik = st.selectbox(etiket, secenekler)
    
    # Seçilen konuya dair bilgi ver
    if mod_secimi == "Meslek Lisesi Sınavları":
        st.warning(f"📌 **Kapsanan Dersler:** {', '.join(MESLEK_GRUPLARI[secilen_alt_baslik])}")
    else:
        st.warning("📌 **İçerik:** Son 5 yılın ÖSYM/TYT soruları baz alınarak hazırlanmıştır.")

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
        with st.status("Yapay Zeka Soruları Hazırlıyor... (15 Soru)", expanded=True):
            sorular = soru_uret(st.session_state.kimlik['mod'], st.session_state.kimlik['baslik'])
            st.session_state.soru_listesi = sorular
            st.session_state.oturum_basladi = True
            st.session_state.yukleniyor = False
            st.rerun()

# SORU EKRANI
elif st.session_state.index < len(st.session_state.soru_listesi):
    soru = st.session_state.soru_listesi[st.session_state.index]
    toplam = len(st.session_state.soru_listesi)
    st.progress((st.session_state.index + 1) / toplam)
    
    st.markdown(f"**{st.session_state.kimlik['baslik']}** | Soru {st.session_state.index + 1} / {toplam}")
    st.markdown(f"<div class='big-font'>{soru['soru']}</div>", unsafe_allow_html=True)
    
    secenekler = soru["secenekler"]
    random.shuffle(secenekler) # Şıkları karıştır
    
    for sec in secenekler:
        if st.button(sec, use_container_width=True):
            if sec == soru["cevap"]:
                st.session_state.puan += (100 / 15) # 15 soruya göre puanlama
                st.toast("✅ Doğru!", icon="🎉")
            else:
                st.toast(f"❌ Yanlış! Cevap: {soru['cevap']}", icon="⚠️")
            time.sleep(1)
            st.session_state.index += 1
            st.rerun()

# SONUÇ EKRANI
else:
    st.balloons()
    final_puan = int(st.session_state.puan)
    st.markdown(f"""
    <div style='background-color:#FF7043; padding:30px; border-radius:15px; text-align:center; color:white; box-shadow: 0 10px 20px rgba(0,0,0,0.2);'>
        <h2>{st.session_state.kimlik['ad']} {st.session_state.kimlik['soyad']}</h2>
        <h1 style='font-size: 60px; margin: 10px 0;'>{final_puan}</h1>
        <p style='font-size: 20px;'>{st.session_state.kimlik['baslik']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.kayit_ok:
        if sonuclari_kaydet(st.session_state.kimlik["ad"], st.session_state.kimlik["soyad"], st.session_state.kimlik["mod"], st.session_state.kimlik["baslik"], final_puan):
            st.success("Sonuç Öğretmenine İletildi ✅")
            st.session_state.kayit_ok = True
            
    if st.button("Ana Menüye Dön"):
        st.session_state.oturum_basladi = False
        st.rerun()
