import streamlit as st
import random
import os
import fitz  # PyMuPDF kütüphanesi

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Bağarası Hibrit Eğitim Merkezi", page_icon="🎓", layout="wide")

# --- TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #F0F4C3 !important; }
    h1, h2, h3, h4, .stMarkdown { color: #212121 !important; }
    
    /* Optik Form Alanı */
    .optik-alan {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #FF7043;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        position: sticky; 
        top: 20px; 
    }
    
    /* Butonlar */
    .stButton>button {
        background-color: #FF7043 !important;
        color: white !important;
        border-radius: 8px;
        font-weight: bold;
        width: 100%;
        border: 2px solid #D84315 !important;
    }
    .stButton>button:hover {
        background-color: #E64A19 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 📝 PDF HARİTASI (SİZİN GÖNDERDİĞİNİZ TAM LİSTE)
# ==============================================================================

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
    344: {"ders": "Kimya", "cevaplar": "DAAD"},
    345: {"ders": "Kimya", "cevaplar": "ADC"},
    346: {"ders": "Kimya", "cevaplar": "CCD"},
    348: {"ders": "Kimya", "cevaplar": "CAC"},
    349: {"ders": "Kimya", "cevaplar": "AEC"},
    350: {"ders": "Kimya", "cevaplar": "BDEB"},
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

# PDF DOSYA ADI
PDF_DOSYA_ADI = "tytson8pdf"

# ==============================================================================
# PDF GÖSTERİCİ
# ==============================================================================
def pdf_sayfa_getir(dosya_yolu, sayfa_numarasi):
    if not os.path.exists(dosya_yolu):
        st.error(f"⚠️ HATA: '{dosya_yolu}' bulunamadı! Lütfen dosyayı GitHub'a yüklediğinizden emin olun.")
        return

    try:
        doc = fitz.open(dosya_yolu)
        
        # Sayfa sınır kontrolü
        if sayfa_numarasi > len(doc) or sayfa_numarasi < 1:
            st.error(f"Hata: İstenen sayfa ({sayfa_numarasi}) PDF sınırları dışında. (Toplam sayfa: {len(doc)})")
            return

        # Sayfayı yükle (0 tabanlı index)
        page = doc.load_page(sayfa_numarasi - 1)
        
        # Yüksek çözünürlüklü resim oluştur
        pix = page.get_pixmap(dpi=150)
        
        # Resmi göster
        st.image(pix.tobytes(), caption=f"Sayfa {sayfa_numarasi}", use_container_width=True)
        
    except Exception as e:
        st.error(f"PDF okuma hatası: {e}")

# ==============================================================================
# EKRAN AKIŞI
# ==============================================================================

if 'oturum' not in st.session_state: st.session_state.oturum = False
if 'secilen_sayfalar' not in st.session_state: st.session_state.secilen_sayfalar = []
if 'aktif_index' not in st.session_state: st.session_state.aktif_index = 0
if 'toplam_puan' not in st.session_state: st.session_state.toplam_puan = 0
if 'cevaplarim' not in st.session_state: st.session_state.cevaplarim = {}

# --- 1. GİRİŞ EKRANI ---
if not st.session_state.oturum:
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2997/2997321.png", width=120)
        st.title("TYT Kampı")
        
        # Mevcut dersleri listele
        mevcut_dersler = sorted(list(set(v["ders"] for v in PDF_HARITASI.values())))
        # Meslek dersi seçeneğini kaldırıp sadece PDF'teki dersleri koyuyoruz
        secenekler = ["Karışık Deneme"] + mevcut_dersler
        
        secilen_ders = st.selectbox("Ders Seçiniz:", secenekler)
        sayfa_sayisi = st.slider("Kaç Sayfa Soru Çözeceksiniz?", 1, 20, 3)
        
        if st.button("Sınavı Başlat 🚀"):
            uygun_sayfalar = []
            for sayfa, detay in PDF_HARITASI.items():
                if secilen_ders == "Karışık Deneme" or detay["ders"] == secilen_ders:
                    uygun_sayfalar.append(sayfa)
            
            if not uygun_sayfalar:
                st.warning(f"⚠️ '{secilen_ders}' için tanımlı sayfa bulunamadı.")
            else:
                random.shuffle(uygun_sayfalar)
                st.session_state.secilen_sayfalar = uygun_sayfalar[:sayfa_sayisi]
                st.session_state.oturum = True
                st.session_state.aktif_index = 0
                st.session_state.toplam_puan = 0
                st.session_state.cevaplarim = {}
                st.rerun()

    st.markdown("# 📚 Bağarası ÇPAL Dijital Sınav Merkezi")
    st.info("Sol menüden ders seçerek PDF üzerindeki gerçek çıkmış soruları çözebilirsiniz.")

# --- 2. SINAV EKRANI ---
elif st.session_state.aktif_index < len(st.session_state.secilen_sayfalar):
    
    suanki_sayfa = st.session_state.secilen_sayfalar[st.session_state.aktif_index]
    veri = PDF_HARITASI[suanki_sayfa]
    ders_adi = veri["ders"]
    dogru_cevaplar = veri["cevaplar"]
    soru_sayisi = len(dogru_cevaplar)
    
    # Ekran Düzeni
    col_pdf, col_form = st.columns([2.5, 1])
    
    with col_pdf:
        st.markdown(f"### 📄 {ders_adi} - Sayfa {suanki_sayfa}")
        pdf_sayfa_getir(PDF_DOSYA_ADI, suanki_sayfa)
        
    with col_form:
        st.markdown("<div class='optik-alan'>", unsafe_allow_html=True)
        st.subheader("📝 Cevap Kağıdı")
        
        dogru_sayisi = 0
        
        with st.form(key=f"form_{suanki_sayfa}"):
            for i in range(soru_sayisi):
                st.write(f"**Soru {i+1}**")
                key = f"c_{suanki_sayfa}_{i}"
                st.radio(f"Soru {i+1}", ["A", "B", "C", "D", "E"], key=key, horizontal=True, label_visibility="collapsed", index=None)
                st.write("---")
            
            if st.form_submit_button("Sayfayı Bitir ve Kontrol Et ✅"):
                for i in range(soru_sayisi):
                    val = st.session_state.get(f"c_{suanki_sayfa}_{i}")
                    dogru = dogru_cevaplar[i]
                    
                    if val == dogru:
                        dogru_sayisi += 1
                        st.toast(f"Soru {i+1}: Doğru! 🎉")
                    elif val:
                        st.toast(f"Soru {i+1}: Yanlış! (Cevap: {dogru})", icon="⚠️")
                    else:
                        st.toast(f"Soru {i+1}: Boş (Cevap: {dogru})", icon="⚪")
                
                # Puanlama
                st.session_state.toplam_puan += (dogru_sayisi * 5)
                st.success(f"Bu sayfada {dogru_sayisi} doğru yaptınız.")
                time.sleep(2)
                st.session_state.aktif_index += 1
                st.rerun()
                
        st.markdown("</div>", unsafe_allow_html=True)

# --- 3. SONUÇ EKRANI ---
else:
    st.balloons()
    st.markdown(f"""
    <div style='background-color:#FF7043; padding:50px; border-radius:20px; text-align:center; color:white;'>
        <h1>🏁 Sınav Bitti!</h1>
        <h2 style='font-size:60px;'>Toplam Puan: {st.session_state.toplam_puan}</h2>
        <p>Tüm seçilen sayfalar başarıyla tamamlandı.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("🔄 Ana Menüye Dön"):
            st.session_state.oturum = False
            st.rerun()
