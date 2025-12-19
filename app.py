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
    3: {"ders": "Türkçe", "cevaplar": "ADCBE"},  # Sayfa 3'te 5 soru var (A,D,C,B,E)
    4: {"ders": "Türkçe", "cevaplar": "CCDA"},   # Sayfa 4'te 4 soru var
    5: {"ders": "Türkçe", "cevaplar": "EBCA"},
    
    # --- SOSYAL BİLİMLER ÖRNEKLERİ ---
    15: {"ders": "Tarih", "cevaplar": "ABCDE"}, 
    16: {"ders": "Coğrafya", "cevaplar": "EDCBA"},
    17: {"ders": "Felsefe", "cevaplar": "CCDAA"},
    
    # --- MATEMATİK ÖRNEKLERİ ---
    25: {"ders": "Matematik", "cevaplar": "AAABB"},
    26: {"ders": "Matematik", "cevaplar": "CCDDD"},
    
    # --- FEN BİLİMLERİ ÖRNEKLERİ ---
    35: {"ders": "Fizik", "cevaplar": "EEAAB"},
    36: {"ders": "Kimya", "cevaplar": "CCBBA"},
    37: {"ders": "Biyoloji", "cevaplar": "DDDEE"},
    
    # Kendi PDF'inize bakarak burayı istediğiniz kadar uzatabilirsiniz...
    # 40: {"ders": "Fizik", "cevaplar": "ACD"}, gibi...
}

# Yüklediğiniz PDF dosyasının tam adı (Değişirse burayı da değiştirin)
PDF_DOSYA_ADI = "tytson7.pdf"

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
