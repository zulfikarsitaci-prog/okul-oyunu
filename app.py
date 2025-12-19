import streamlit as st
import base64
import random

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Bağarası Hibrit Eğitim Merkezi", page_icon="🎓", layout="wide")

# --- TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #F0F4C3 !important; }
    h1, h2, h3, h4, .stMarkdown { color: #212121 !important; }
    
    /* PDF Alanı */
    iframe {
        border: 4px solid #FF7043;
        border-radius: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    
    /* Optik Form */
    .optik-alan {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #AED581;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Butonlar */
    .stButton>button {
        background-color: #FF7043 !important;
        color: white !important;
        border-radius: 8px;
        font-weight: bold;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #E64A19 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 📝 BURAYI DOLDURMANIZ YETERLİ (CEVAP ANAHTARI MERKEZİ)
# ==============================================================================
# Format:  Sayfa_No: {"ders": "Ders Adı", "cevaplar": "Cevaplar_Bitişik_Yazılır"}
# ÖNEMLİ: PDF'teki sayfa numarası ile buradaki numara tutmalıdır.

PDF_HARITASI = {
    # --- TÜRKÇE ÖRNEKLERİ ---
    13: {"ders": "Türkçe", "cevaplar": "ECE"},  # Sayfa 3'te 5 soru var (A,D,C,B,E)
    14: {"ders": "Türkçe", "cevaplar": "BAC"},   # Sayfa 4'te 4 soru var
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
    25: {"ders": "Türkçe", "cevaplar": "EAB"} 
    26: {"ders": "Türkçe", "cevaplar": "CD"} 
    27: {"ders": "Türkçe", "cevaplar": "CDA"} 
    28: {"ders": "Türkçe", "cevaplar": "DD"} 
    29: {"ders": "Türkçe", "cevaplar": "BD"} 
    30: {"ders": "Türkçe", "cevaplar": "BDA"} 
    31: {"ders": "Türkçe", "cevaplar": "EAD"} 
    32: {"ders": "Türkçe", "cevaplar": "AB"} 
    33: {"ders": "Türkçe", "cevaplar": "BAA"} 
    34: {"ders": "Türkçe", "cevaplar": "DCB"} 
    35: {"ders": "Türkçe", "cevaplar": "CAD"} 
    36: {"ders": "Türkçe", "cevaplar": "DDB"} 
    37: {"ders": "Türkçe", "cevaplar": "CBD"} 
    38: {"ders": "Türkçe", "cevaplar": "AA"} 
    39: {"ders": "Türkçe", "cevaplar": "EBE"} 
    40: {"ders": "Türkçe", "cevaplar": "BDE"} 
    41: {"ders": "Türkçe", "cevaplar": "ADA"} 
    42: {"ders": "Türkçe", "cevaplar": "CDB"} 
    43: {"ders": "Türkçe", "cevaplar": "AC"} 
    44: {"ders": "Türkçe", "cevaplar": "DEA"} 
    112: {"ders": "Türkçe", "cevaplar": "DA"} 
    111: {"ders": "Türkçe", "cevaplar": "EC"} 
    110: {"ders": "Türkçe", "cevaplar": "BC"} 
    109: {"ders": "Türkçe", "cevaplar": "EDD"} 
    108: {"ders": "Türkçe", "cevaplar": "AC"} 
    107: {"ders": "Türkçe", "cevaplar": "BC"} 
    103: {"ders": "Türkçe", "cevaplar": "AA"} 
    102: {"ders": "Türkçe", "cevaplar": "CEC"} 
    101: {"ders": "Türkçe", "cevaplar": "ED"} 
    100: {"ders": "Türkçe", "cevaplar": "BB"} 
    99: {"ders": "Türkçe", "cevaplar": "EA"} 
    98: {"ders": "Türkçe", "cevaplar": "EB"} 
    97: {"ders": "Türkçe", "cevaplar": "DC"} 
    93: {"ders": "Türkçe", "cevaplar": "CB"} 
    92: {"ders": "Türkçe", "cevaplar": "BAA"} 
    91: {"ders": "Türkçe", "cevaplar": "DC"} 
    90: {"ders": "Türkçe", "cevaplar": "AB"} 
    89: {"ders": "Türkçe", "cevaplar": "EE"} 
    88: {"ders": "Türkçe", "cevaplar": "CD"} 
    121: {"ders": "Türkçe", "cevaplar": "DCED"} 
    122: {"ders": "Türkçe", "cevaplar": "DEDB"} 
    123: {"ders": "Türkçe", "cevaplar": "ABA"} 
    124: {"ders": "Türkçe", "cevaplar": "EEDA"} 
    125: {"ders": "Türkçe", "cevaplar": "DAC"} 
    126: {"ders": "Türkçe", "cevaplar": "CBAE"} 
    127: {"ders": "Türkçe", "cevaplar": "DEB"} 
    128: {"ders": "Türkçe", "cevaplar": "BDDB"} 
    129: {"ders": "Türkçe", "cevaplar": "CBCE"} 
    130: {"ders": "Türkçe", "cevaplar": "CCCC"} 
    131: {"ders": "Türkçe", "cevaplar": "DEDD"} 
    132: {"ders": "Türkçe", "cevaplar": "BCCC"} 
    133: {"ders": "Türkçe", "cevaplar": "C"} 
   
    
    # --- SOSYAL BİLİMLER ÖRNEKLERİ ---
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


    168: {"ders": "Felsefe", "cevaplar": "CD"},
     169: {"ders": "Felsefe", "cevaplar": "BD"},
      170: {"ders": "Felsefe", "cevaplar": "EB"},
      171: {"ders": "Felsefe", "cevaplar": "BE"},
      172: {"ders": "Felsefe", "cevaplar": "BB"},
      173: {"ders": "Felsefe", "cevaplar": "BAA"},
      174: {"ders": "Felsefe", "cevaplar": "BDD"},
      175: {"ders": "Felsefe", "cevaplar": "AAB"},
     176: {"ders": "Felsefe", "cevaplar": "DA"},
   
    
    # --- MATEMATİK ÖRNEKLERİ ---
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
    
      
    # --- FEN BİLİMLERİ ÖRNEKLERİ ---
    312: {"ders": "Fizik", "cevaplar": "EBC"},
 313: {"ders": "Fizik", "cevaplar": "BA"},
314: {"ders": "Fizik", "cevaplar": "EDE"},
316: {"ders": "Fizik", "cevaplar": "DAE"},
317: {"ders": "Fizik", "cevaplar": "BDEA"},
318: {"ders": "Fizik", "cevaplar": "DDD"},
320: {"ders": "Fizik", "cevaplar": "ABE"},
321: {"ders": "Fizik", "cevaplar": "ADA"},


    339: {"ders": "Kimya", "cevaplar": "ACAE"},
340: {"ders": "Kimya", "cevaplar": "BC"},
350: {"ders": "Kimya", "cevaplar": "BDEB"},
344: {"ders": "Kimya", "cevaplar": "DAAD"},
345: {"ders": "Kimya", "cevaplar": "ADC"},
346: {"ders": "Kimya", "cevaplar": "CCD"},
348: {"ders": "Kimya", "cevaplar": "CAC"},
349: {"ders": "Kimya", "cevaplar": "AEC"},
351: {"ders": "Kimya", "cevaplar": "AAB"},




    359: {"ders": "Biyoloji", "cevaplar": "CBEE"},
360: {"ders": "Biyoloji", "cevaplar": "DADC"},
361: {"ders": "Biyoloji", "cevaplar": "BBD"},
362: {"ders": "Biyoloji", "cevaplar": "AEDB"},
363: {"ders": "Biyoloji", "cevaplar": "ECB"},
365: {"ders": "Biyoloji", "cevaplar": "AEC"},
373: {"ders": "Biyoloji", "cevaplar": "DE"},
374: {"ders": "Biyoloji", "cevaplar": "EEE"},

    
    # Kendi PDF'inize bakarak burayı istediğiniz kadar uzatabilirsiniz...
    # 40: {"ders": "Fizik", "cevaplar": "ACD"}, gibi...
}

# Yüklediğiniz PDF dosyasının tam adı (Değişirse burayı da değiştirin)
PDF_DOSYA_ADI = "tytson8.pdf"

# ==============================================================================
# PDF GÖSTERME FONKSİYONU
# ==============================================================================
def pdf_goster(dosya_yolu, sayfa_no):
    try:
        with open(dosya_yolu, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        # PDF'i embed et ve sayfa numarasına yönlendir (#page=X)
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}#page={sayfa_no}" width="100%" height="850" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"⚠️ PDF Dosyası ({PDF_DOSYA_ADI}) Bulunamadı! Dosyayı GitHub'a yüklediğinizden emin olun.")

# ==============================================================================
# EKRAN AKIŞI
# ==============================================================================

# Session State (Hafıza) Tanımları
if 'oturum' not in st.session_state: st.session_state.oturum = False
if 'secilen_sayfalar' not in st.session_state: st.session_state.secilen_sayfalar = []
if 'aktif_index' not in st.session_state: st.session_state.aktif_index = 0
if 'toplam_puan' not in st.session_state: st.session_state.toplam_puan = 0
if 'cevaplarim' not in st.session_state: st.session_state.cevaplarim = {}

# --- 1. GİRİŞ EKRANI (SOL MENÜ) ---
if not st.session_state.oturum:
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2997/2997321.png", width=120)
        st.title("TYT Kampı Giriş")
        st.info("Bağarası ÇPAL - Dijital Sınav Merkezi")
        
        # Ders Seçimi
        dersler = ["Karışık Deneme", "Türkçe", "Matematik", "Tarih", "Coğrafya", "Fizik", "Kimya", "Biyoloji", "Felsefe"]
        secilen_ders = st.selectbox("Çözmek İstediğiniz Ders:", dersler)
        
        # Soru Sayısı (Sayfa Bazlı)
        sayfa_sayisi = st.slider("Kaç Sayfa Soru Çözeceksiniz?", 1, 10, 3)
        
        if st.button("Sınavı Başlat 🚀"):
            # Havuzdan uygun sayfaları bul
            uygun_sayfalar = []
            for sayfa, detay in PDF_HARITASI.items():
                if secilen_ders == "Karışık Deneme" or detay["ders"] == secilen_ders:
                    uygun_sayfalar.append(sayfa)
            
            if not uygun_sayfalar:
                st.warning(f"Henüz '{secilen_ders}' dersi için sisteme sayfa tanımlanmamış. Lütfen 'PDF_HARITASI' kısmını güncelleyin.")
            else:
                # Rastgele sayfalar seç
                random.shuffle(uygun_sayfalar)
                # İstenilen adetten fazla sayfa varsa kes, azsa hepsini al
                st.session_state.secilen_sayfalar = uygun_sayfalar[:sayfa_sayisi]
                
                # Sınavı Başlat
                st.session_state.oturum = True
                st.session_state.aktif_index = 0
                st.session_state.toplam_puan = 0
                st.session_state.cevaplarim = {}
                st.rerun()

    # Ana Sayfa Karşılama
    st.markdown("""
    # 📚 Gerçek Çıkmış Sorularla Sınav Kampı
    
    Bu sistem, elinizdeki **Çıkmış Sorular Kitapçığını (PDF)** interaktif bir sınava dönüştürür.
    
    ### 🎯 Nasıl Kullanılır?
    1. Sol menüden **Ders** seçin.
    2. Sistem size rastgele bir **PDF Sayfası** getirecek.
    3. Sorular **orijinal görüntüleriyle** (Resim, Grafik, Tablo) karşınızda olacak.
    4. Yandaki **Sanal Optik Form**'a cevaplarınızı işaretleyin.
    5. Anında sonucunuzu öğrenin!
    """)

# --- 2. SINAV EKRANI ---
elif st.session_state.aktif_index < len(st.session_state.secilen_sayfalar):
    
    # Şu anki sayfa bilgilerini al
    suanki_sayfa = st.session_state.secilen_sayfalar[st.session_state.aktif_index]
    veri = PDF_HARITASI[suanki_sayfa]
    ders_adi = veri["ders"]
    dogru_cevap_anahtari = veri["cevaplar"] # Örn: "ADCB"
    soru_sayisi = len(dogru_cevap_anahtari)
    
    # Ekranı Böl: PDF (Geniş) | Optik Form (Dar)
    col_pdf, col_form = st.columns([2.5, 1])
    
    with col_pdf:
        st.markdown(f"### 📄 {ders_adi} - Sayfa {suanki_sayfa}")
        pdf_goster(PDF_DOSYA_ADI, suanki_sayfa)
        
    with col_form:
        st.markdown("<div class='optik-alan'>", unsafe_allow_html=True)
        st.subheader("📝 Cevap Kağıdı")
        
        sayfa_puani = 0
        dogru_sayisi = 0
        
        # Formu Oluştur
        with st.form(key=f"form_{suanki_sayfa}"):
            for i in range(soru_sayisi):
                st.write(f"**Soru {i+1}**")
                # Radyo butonları (A, B, C, D, E)
                st.radio(f"Soru {i+1}", ["A", "B", "C", "D", "E"], key=f"c_{suanki_sayfa}_{i}", horizontal=True, label_visibility="collapsed", index=None)
                st.write("---")
            
            # Kontrol Butonu
            if st.form_submit_button("Sayfayı Bitir ve Kontrol Et ✅"):
                # Cevapları Kontrol Et
                for i in range(soru_sayisi):
                    kullanici_cevabi = st.session_state.get(f"c_{suanki_sayfa}_{i}")
                    gercek_cevap = dogru_cevap_anahtari[i]
                    
                    if kullanici_cevabi == gercek_cevap:
                        dogru_sayisi += 1
                        st.toast(f"Soru {i+1}: Doğru! 🎉")
                    elif kullanici_cevabi:
                        st.toast(f"Soru {i+1}: Yanlış! (Cevap: {gercek_cevap})", icon="⚠️")
                    else:
                        st.toast(f"Soru {i+1}: Boş Bırakıldı (Cevap: {gercek_cevap})", icon="⚪")
                
                # Puanlama (Örn: Soru başı 5 puan)
                sayfa_puani = dogru_sayisi * 5
                st.session_state.toplam_puan += sayfa_puani
                
                # Bildirim ve Geçiş
                st.success(f"Sayfa Sonucu: {dogru_sayisi} / {soru_sayisi} Doğru")
                time.sleep(2) # Sonucu görmesi için bekle
                st.session_state.aktif_index += 1
                st.rerun()
                
        st.markdown("</div>", unsafe_allow_html=True)

# --- 3. SONUÇ EKRANI ---
else:
    st.balloons()
    st.markdown(f"""
    <div style='background-color:#FF7043; padding:50px; border-radius:20px; text-align:center; color:white;'>
        <h1>🏁 Sınav Tamamlandı!</h1>
        <h2 style='font-size:60px;'>Toplam Puan: {st.session_state.toplam_puan}</h2>
        <p>Tüm seçilen sayfalar başarıyla çözüldü.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("🔄 Ana Menüye Dön"):
            st.session_state.oturum = False
            st.rerun()
