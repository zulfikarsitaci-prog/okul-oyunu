import streamlit as st
import random
import os
import time
import json
import fitz  # PyMuPDF
import google.generativeai as genai

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Bağarası Hibrit Eğitim Merkezi", page_icon="🎓", layout="wide")

# --- API KEY KONTROLÜ (Meslek Soruları İçin) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #F0F4C3 !important; }
    h1, h2, h3, h4, .stMarkdown { color: #212121 !important; }
    
    /* Optik Form Alanı */
    .optik-alan {
        background-color: white;
        padding: 15px;
        border-radius: 15px;
        border: 2px solid #FF7043;
        margin-bottom: 20px;
    }
    
    /* Butonlar */
    .stButton>button {
        background-color: #FF7043 !important;
        color: white !important;
        border-radius: 8px;
        font-weight: bold;
        width: 100%;
        border: 2px solid #D84315 !important;
        min-height: 50px;
    }
    .stButton>button:hover {
        background-color: #E64A19 !important;
    }
    
    /* Sekme (Tab) Tasarımı */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #FFFFFF;
        border-radius: 5px;
        padding: 10px 20px;
        border: 1px solid #FF7043;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FF7043 !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 1. VERİ HAVUZLARI
# ==============================================================================

# A) MESLEK LİSESİ KONULARI (Yapay Zeka Üretecek)
MESLEK_KONULARI = {
    "9. Sınıf Meslek": "Temel Muhasebe, Mesleki Matematik, Ofis Programları",
    "10. Sınıf Meslek": "Genel Muhasebe, Klavye Teknikleri, Hukuk",
    "11. Sınıf Meslek": "Şirketler Muhasebesi, Maliyet, Vergi",
    "12. Sınıf Meslek": "Girişimcilik, Finansal Okuryazarlık"
}

# B) TYT PDF HARİTASI (PDF'ten Çekilecek)
PDF_HARITASI = {
    # --- TÜRKÇE ---
    13: {"ders": "Türkçe", "cevaplar": "ECE"},
    14: {"ders": "Türkçe", "cevaplar": "BAC"},
    15: {"ders": "Türkçe", "cevaplar": "BEA"},
    16: {"ders": "Türkçe", "cevaplar": "CBCD"},
    17: {"ders": "Türkçe", "cevaplar": "AABA"},
    18: {"ders": "Türkçe", "cevaplar": "CEA"},
    19: {"ders": "Türkçe", "cevaplar": "EBA"},
    20: {"ders": "Türkçe", "cevaplar": "ADB"},
    21: {"ders": "Türkçe", "cevaplar": "CBBE"},
    22: {"ders": "Türkçe", "cevaplar": "BB"},
    23: {"ders": "Türkçe", "cevaplar": "BEA"},
    24: {"ders": "Türkçe", "cevaplar": "ADE"},
    25: {"ders": "Türkçe", "cevaplar": "EAB"}, 
    26: {"ders": "Türkçe", "cevaplar": "CD"},
    27: {"ders": "Türkçe", "cevaplar": "CDA"}, 
    28: {"ders": "Türkçe", "cevaplar": "DD"},
    29: {"ders": "Türkçe", "cevaplar": "BD"}, 
    30: {"ders": "Türkçe", "cevaplar": "BDA"}, 
    31: {"ders": "Türkçe", "cevaplar": "EAD"}, 
    32: {"ders": "Türkçe", "cevaplar": "AB"}, 
    33: {"ders": "Türkçe", "cevaplar": "BAA"}, 
    34: {"ders": "Türkçe", "cevaplar": "DCB"}, 
    35: {"ders": "Türkçe", "cevaplar": "CAD"}, 
    36: {"ders": "Türkçe", "cevaplar": "DDB"}, 
    37: {"ders": "Türkçe", "cevaplar": "CBD"}, 
    38: {"ders": "Türkçe", "cevaplar": "AA"}, 
    39: {"ders": "Türkçe", "cevaplar": "EBE"}, 
    40: {"ders": "Türkçe", "cevaplar": "BDE"}, 
    41: {"ders": "Türkçe", "cevaplar": "ADA"}, 
    42: {"ders": "Türkçe", "cevaplar": "CDB"}, 
    43: {"ders": "Türkçe", "cevaplar": "AC"}, 
    44: {"ders": "Türkçe", "cevaplar": "DEA"}, 
    88: {"ders": "Türkçe", "cevaplar": "CD"}, 
    89: {"ders": "Türkçe", "cevaplar": "EE"}, 
    90: {"ders": "Türkçe", "cevaplar": "AB"}, 
    91: {"ders": "Türkçe", "cevaplar": "DC"}, 
    92: {"ders": "Türkçe", "cevaplar": "BAA"}, 
    93: {"ders": "Türkçe", "cevaplar": "CB"}, 
    97: {"ders": "Türkçe", "cevaplar": "DC"}, 
    98: {"ders": "Türkçe", "cevaplar": "EB"}, 
    99: {"ders": "Türkçe", "cevaplar": "EA"}, 
    100: {"ders": "Türkçe", "cevaplar": "BB"}, 
    101: {"ders": "Türkçe", "cevaplar": "ED"}, 
    102: {"ders": "Türkçe", "cevaplar": "CEC"}, 
    103: {"ders": "Türkçe", "cevaplar": "AA"}, 
    107: {"ders": "Türkçe", "cevaplar": "BC"}, 
    108: {"ders": "Türkçe", "cevaplar": "AC"}, 
    109: {"ders": "Türkçe", "cevaplar": "EDD"}, 
    110: {"ders": "Türkçe", "cevaplar": "BC"}, 
    111: {"ders": "Türkçe", "cevaplar": "EC"}, 
    112: {"ders": "Türkçe", "cevaplar": "DA"}, 
    121: {"ders": "Türkçe", "cevaplar": "DCED"}, 
    122: {"ders": "Türkçe", "cevaplar": "DEDB"}, 
    123: {"ders": "Türkçe", "cevaplar": "ABA"}, 
    124: {"ders": "Türkçe", "cevaplar": "EEDA"}, 
    125: {"ders": "Türkçe", "cevaplar": "DAC"}, 
    126: {"ders": "Türkçe", "cevaplar": "CBAE"}, 
    127: {"ders": "Türkçe", "cevaplar": "DEB"}, 
    128: {"ders": "Türkçe", "cevaplar": "BDDB"}, 
    129: {"ders": "Türkçe", "cevaplar": "CBCE"}, 
    130: {"ders": "Türkçe", "cevaplar": "CCCC"}, 
    131: {"ders": "Türkçe", "cevaplar": "DEDD"}, 
    132: {"ders": "Türkçe", "cevaplar": "BCCC"}, 
    133: {"ders": "Türkçe", "cevaplar": "C"}, 

    # --- TARİH ---
    138: {"ders": "Tarih", "cevaplar": "BDEE"},
    139: {"ders": "Tarih", "cevaplar": "CEDA"}, 
    140: {"ders": "Tarih", "cevaplar": "CADC"}, 
    141: {"ders": "Tarih", "cevaplar": "CEEE"}, 
    142: {"ders": "Tarih", "cevaplar": "DED"}, 
    143: {"ders": "Tarih", "cevaplar": "AE"}, 
    144: {"ders": "Tarih", "cevaplar": "BABC"}, 
    145: {"ders": "Tarih", "cevaplar": "ADCE"}, 
    146: {"ders": "Tarih", "cevaplar": "BCBD"}, 
    147: {"ders": "Tarih", "cevaplar": "CBCE"}, 
    148: {"ders": "Tarih", "cevaplar": "ACE"}, 

    # --- COĞRAFYA ---
    151: {"ders": "Coğrafya", "cevaplar": "CACE"},
    152: {"ders": "Coğrafya", "cevaplar": "AAB"},
    153: {"ders": "Coğrafya", "cevaplar": "BBB"},
    154: {"ders": "Coğrafya", "cevaplar": "BBAA"}, 
    155: {"ders": "Coğrafya", "cevaplar": "CBC"},
    156: {"ders": "Coğrafya", "cevaplar": "ECA"},
    157: {"ders": "Coğrafya", "cevaplar": "CD"}, 
    158: {"ders": "Coğrafya", "cevaplar": "EC"},
    159: {"ders": "Coğrafya", "cevaplar": "AC"},
    160: {"ders": "Coğrafya", "cevaplar": "EEDE"},
    161: {"ders": "Coğrafya", "cevaplar": "DCBD"},
    162: {"ders": "Coğrafya", "cevaplar": "CDDD"},
    163: {"ders": "Coğrafya", "cevaplar": "CD"},

    # --- FELSEFE ---
    168: {"ders": "Felsefe", "cevaplar": "CD"},
    169: {"ders": "Felsefe", "cevaplar": "BD"},
    170: {"ders": "Felsefe", "cevaplar": "EB"},
    171: {"ders": "Felsefe", "cevaplar": "BE"},
    172: {"ders": "Felsefe", "cevaplar": "BB"},
    173: {"ders": "Felsefe", "cevaplar": "BAA"},
    174: {"ders": "Felsefe", "cevaplar": "BDD"},
    175: {"ders": "Felsefe", "cevaplar": "AAB"},
    176: {"ders": "Felsefe", "cevaplar": "DA"},

    # --- MATEMATİK ---
    213: {"ders": "Matematik", "cevaplar": "AEB"},
    214: {"ders": "Matematik", "cevaplar": "ECA"},
    215: {"ders": "Matematik", "cevaplar": "CDCE"},
    216: {"ders": "Matematik", "cevaplar": "DDCD"},
    217: {"ders": "Matematik", "cevaplar": "AEC"},
    218: {"ders": "Matematik", "cevaplar": "CAA"},
    219: {"ders": "Matematik", "cevaplar": "BEAB"},
    221: {"ders": "Matematik", "cevaplar": "DEAA"},
    222: {"ders": "Matematik", "cevaplar": "BBC"},
    226: {"ders": "Matematik", "cevaplar": "ABAE"},
    227: {"ders": "Matematik", "cevaplar": "CBB"},
    230: {"ders": "Matematik", "cevaplar": "BCCD"},
    231: {"ders": "Matematik", "cevaplar": "DADB"},
    232: {"ders": "Matematik", "cevaplar": "EE"},
    246: {"ders": "Matematik", "cevaplar": "CCB"},
    247: {"ders": "Matematik", "cevaplar": "EACE"},
    249: {"ders": "Matematik", "cevaplar": "DAAC"},
    250: {"ders": "Matematik", "cevaplar": "BE"},

    # --- FİZİK ---
    312: {"ders": "Fizik", "cevaplar": "EBC"},
    313: {"ders": "Fizik", "cevaplar": "BA"},
    314: {"ders": "Fizik", "cevaplar": "EDE"},
    316: {"ders": "Fizik", "cevaplar": "DAE"},
    317: {"ders": "Fizik", "cevaplar": "BDEA"},
    318: {"ders": "Fizik", "cevaplar": "DDD"},
    320: {"ders": "Fizik", "cevaplar": "ABE"},
    321: {"ders": "Fizik", "cevaplar": "ADA"},

    # --- KİMYA ---
    339: {"ders": "Kimya", "cevaplar": "ACAE"},
    340: {"ders": "Kimya", "cevaplar": "BC"},
    350: {"ders": "Kimya", "cevaplar": "BDEB"},
    344: {"ders": "Kimya", "cevaplar": "DAAD"},
    345: {"ders": "Kimya", "cevaplar": "ADC"},
    346: {"ders": "Kimya", "cevaplar": "CCD"},
    348: {"ders": "Kimya", "cevaplar": "CAC"},
    349: {"ders": "Kimya", "cevaplar": "AEC"},
    351: {"ders": "Kimya", "cevaplar": "AAB"},

    # --- BİYOLOJİ ---
    359: {"ders": "Biyoloji", "cevaplar": "CBEE"},
    360: {"ders": "Biyoloji", "cevaplar": "DADC"},
    361: {"ders": "Biyoloji", "cevaplar": "BBD"},
    362: {"ders": "Biyoloji", "cevaplar": "AEDB"},
    363: {"ders": "Biyoloji", "cevaplar": "ECB"},
    365: {"ders": "Biyoloji", "cevaplar": "AEC"},
    373: {"ders": "Biyoloji", "cevaplar": "DE"},
    374: {"ders": "Biyoloji", "cevaplar": "EEE"}
}

PDF_DOSYA_ADI = "tytson8.pdf"

# ==============================================================================
# FONKSİYONLAR
# ==============================================================================

# 1. PDF GÖSTERİCİ (PyMuPDF)
def pdf_sayfa_getir(dosya_yolu, sayfa_numarasi):
    if not os.path.exists(dosya_yolu):
        st.error(f"⚠️ PDF Dosyası ({dosya_yolu}) bulunamadı!")
        return
    try:
        doc = fitz.open(dosya_yolu)
        page = doc.load_page(sayfa_numarasi - 1)
        
        # Mobil için varsayılan zoom 150 yeterlidir
        pix = page.get_pixmap(dpi=150)
        st.image(pix.tobytes(), caption=f"Sayfa {sayfa_numarasi}", use_container_width=True)
    except Exception as e:
        st.error(f"Hata: {e}")

# 2. AI SORU ÜRETİCİ (Meslek Lisesi İçin)
def ai_soru_uret(ders_adi):
    if "GOOGLE_API_KEY" not in st.secrets:
        return [{"soru": "API Key Eksik!", "secenekler": ["A"], "cevap": "A"}]
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Rol: Meslek Lisesi Öğretmeni.
        Ders: {ders_adi}
        Görev: 5 adet çoktan seçmeli soru hazırla.
        Format: JSON listesi.
        [ {{"soru": "...", "secenekler": ["A", "B", "C", "D", "E"], "cevap": "Doğru Cevabın Metni"}} ]
        """
        resp = model.generate_content(prompt)
        text = resp.text.strip().replace("```json", "").replace("```", "")
        return json.loads(text)
    except:
        return []

# ==============================================================================
# EKRAN AKIŞI
# ==============================================================================

if 'oturum' not in st.session_state: st.session_state.oturum = False
if 'mod' not in st.session_state: st.session_state.mod = ""
if 'secilen_liste' not in st.session_state: st.session_state.secilen_liste = [] # PDF Sayfaları veya AI Soruları
if 'aktif_index' not in st.session_state: st.session_state.aktif_index = 0
if 'toplam_puan' not in st.session_state: st.session_state.toplam_puan = 0
if 'cevaplarim' not in st.session_state: st.session_state.cevaplarim = {}

# --- GİRİŞ MENÜSÜ ---
if not st.session_state.oturum:
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2997/2997321.png", width=120)
        st.title("Sınav Modu")
        
        mod_secimi = st.radio("Hangisini Çözeceksiniz?", ["TYT Kampı (PDF)", "Meslek Lisesi Sınavları"])
        
        if mod_secimi == "TYT Kampı (PDF)":
            # PDF DERSLERİ
            mevcut = sorted(list(set(v["ders"] for v in PDF_HARITASI.values())))
            ders = st.selectbox("Ders Seç:", ["Karışık Deneme"] + mevcut)
            adet = st.slider("Kaç Sayfa?", 1, 10, 3)
            
            if st.button("TYT Başlat 🚀"):
                # Sayfaları Hazırla
                uygun = []
                for s, d in PDF_HARITASI.items():
                    if ders == "Karışık Deneme" or d["ders"] == ders:
                        uygun.append(s)
                
                if uygun:
                    random.shuffle(uygun)
                    st.session_state.secilen_liste = uygun[:adet]
                    st.session_state.mod = "PDF"
                    st.session_state.oturum = True
                    st.session_state.aktif_index = 0
                    st.session_state.toplam_puan = 0
                    st.rerun()
                else:
                    st.error("Bu ders için sayfa bulunamadı.")
                    
        else:
            # MESLEK SINAVLARI (AI)
            ders = st.selectbox("Alan Seç:", list(MESLEK_KONULARI.keys()))
            if st.button("Meslek Sınavını Başlat 🤖"):
                with st.spinner("Yapay Zeka Soruları Hazırlıyor..."):
                    sorular = ai_soru_uret(MESLEK_KONULARI[ders])
                    st.session_state.secilen_liste = sorular
                    st.session_state.mod = "AI"
                    st.session_state.oturum = True
                    st.session_state.aktif_index = 0
                    st.session_state.toplam_puan = 0
                    st.rerun()

    st.info("👈 Sınavı başlatmak için sol menüyü kullanın.")

# --- SINAV EKRANI ---
elif st.session_state.aktif_index < len(st.session_state.secilen_liste):
    
    # 1. MOD: PDF (TYT)
    if st.session_state.mod == "PDF":
        sayfa_no = st.session_state.secilen_liste[st.session_state.aktif_index]
        veri = PDF_HARITASI[sayfa_no]
        ders_adi = veri["ders"]
        cevaplar = veri["cevaplar"]
        soru_sayisi = len(cevaplar)
        
        st.subheader(f"📄 {ders_adi} - Sayfa {sayfa_no}")
        
        # --- MOBİL DOSTU SEKME SİSTEMİ (TAB) ---
        tab1, tab2 = st.tabs(["📄 SORU KİTAPÇIĞI (Görsel)", "📝 CEVAP KAĞIDI (İşaretle)"])
        
        with tab1:
            # PDF Göster
            pdf_sayfa_getir(PDF_DOSYA_ADI, sayfa_no)
            
        with tab2:
            st.warning("Cevaplarınızı buradan işaretleyin:")
            dogru_sayisi = 0
            with st.form(key=f"form_{sayfa_no}"):
                for i in range(soru_sayisi):
                    st.write(f"**Soru {i+1}**")
                    st.radio(f"S_{i}", ["A", "B", "C", "D", "E"], key=f"c_{sayfa_no}_{i}", horizontal=True, label_visibility="collapsed", index=None)
                    st.divider()
                
                if st.form_submit_button("KONTROL ET VE GEÇ ➡️"):
                    for i in range(soru_sayisi):
                        val = st.session_state.get(f"c_{sayfa_no}_{i}")
                        dogru = cevaplar[i]
                        if val == dogru:
                            dogru_sayisi += 1
                            st.toast(f"{i+1}. Soru: DOĞRU! ✅")
                        else:
                            st.toast(f"{i+1}. Soru: YANLIŞ! (Cevap: {dogru}) ❌")
                    
                    st.session_state.toplam_puan += (dogru_sayisi * 5)
                    time.sleep(2)
                    st.session_state.aktif_index += 1
                    st.rerun()

    # 2. MOD: AI (MESLEK)
    else:
        soru = st.session_state.secilen_liste[st.session_state.aktif_index]
        st.subheader(f"🤖 Soru {st.session_state.aktif_index + 1}")
        
        st.info(soru["soru"])
        
        secenekler = soru["secenekler"]
        random.shuffle(secenekler)
        
        c1, c2 = st.columns(2)
        for i, sec in enumerate(secenekler):
            def click(s=sec, d=soru["cevap"]):
                if s == d:
                    st.toast("Doğru! ✅")
                    st.session_state.toplam_puan += 20
                else:
                    st.toast(f"Yanlış! Cevap: {d} ❌")
                time.sleep(1)
                st.session_state.aktif_index += 1
                
            if i < len(secenekler)/2:
                with c1: st.button(sec, on_click=click, key=f"btn_{st.session_state.aktif_index}_{i}")
            else:
                with c2: st.button(sec, on_click=click, key=f"btn_{st.session_state.aktif_index}_{i}")

# --- SONUÇ EKRANI ---
else:
    st.balloons()
    st.success(f"Sınav Bitti! Toplam Puan: {st.session_state.toplam_puan}")
    if st.button("Başa Dön"):
        st.session_state.oturum = False
        st.rerun()
