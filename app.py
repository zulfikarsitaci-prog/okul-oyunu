import streamlit as st
import time
import random

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Bağarası Finans Ligi", page_icon="🎓", layout="centered")

# --- STİL (CSS) ---
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-weight: bold;
    }
    .success-msg { color: #28a745; font-weight: bold; font-size: 20px; }
    .error-msg { color: #dc3545; font-weight: bold; font-size: 20px; }
    .big-font { font-size: 24px !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- SORU HAVUZU (MUHASEBE & FİNANS) ---
# Buraya istediğiniz kadar soru ekleyebilirsiniz.
tum_sorular = [
    {"soru": "İşletmenin kasasına nakit para girişi olduğunda '100 Kasa Hesabı' nasıl çalışır?", "secenekler": ["Borçlanır (Giriş)", "Alacaklanır (Çıkış)", "Değişmez"], "cevap": "Borçlanır (Giriş)"},
    {"soru": "Satıcıya olan veresiye borcumuzu ödediğimizde hangi hesap BORÇLANIR?", "secenekler": ["320 Satıcılar", "100 Kasa", "120 Alıcılar"], "cevap": "320 Satıcılar"},
    {"soru": "Mal alışı sırasında ödenen Katma Değer Vergisi hangi hesapta izlenir?", "secenekler": ["191 İndirilecek KDV", "391 Hesaplanan KDV", "360 Ödenecek Vergi"], "cevap": "191 İndirilecek KDV"},
    {"soru": "Müşteriden alınan çeklerin izlendiği hesap hangisidir?", "secenekler": ["101 Alınan Çekler", "103 Verilen Çekler", "121 Alacak Senetleri"], "cevap": "101 Alınan Çekler"},
    {"soru": "Banka hesabımızdan para çekildiğinde '102 Bankalar' hesabı nasıl çalışır?", "secenekler": ["Alacaklanır (Azalış)", "Borçlanır (Artış)", "Kapanır"], "cevap": "Alacaklanır (Azalış)"},
    {"soru": "İşletme sahibi sermaye olarak 50.000 TL nakit koymuştur. Alacaklı hesap hangisidir?", "secenekler": ["500 Sermaye", "100 Kasa", "600 Yurt İçi Satışlar"], "cevap": "500 Sermaye"},
    {"soru": "Mal satışı yapıldığında, satış tutarı (gelir) hangi hesabın alacağına yazılır?", "secenekler": ["600 Yurt İçi Satışlar", "153 Ticari Mallar", "391 Hesaplanan KDV"], "cevap": "600 Yurt İçi Satışlar"},
    {"soru": "Aşağıdakilerden hangisi bir 'Varlık' hesabıdır?", "secenekler": ["102 Bankalar", "300 Banka Kredileri", "320 Satıcılar"], "cevap": "102 Bankalar"},
    {"soru": "Senetsiz (veresiye) mal sattığımızda hangi hesap borçlanır?", "secenekler": ["120 Alıcılar", "320 Satıcılar", "100 Kasa"], "cevap": "120 Alıcılar"},
    {"soru": "Dönem sonunda '191 İndirilecek KDV' hesabının bakiyesi, '391 Hesaplanan KDV'den büyükse ne oluşur?", "secenekler": ["Devreden KDV", "Ödenecek KDV", "KDV İadesi"], "cevap": "Devreden KDV"},
    {"soru": "Kısa vadeli yabancı kaynaklar bilançonun hangi grubunda yer alır?", "secenekler": ["3. Grup", "4. Grup", "5. Grup"], "cevap": "3. Grup"},
    {"soru": "Demirbaş alımında ödenen KDV hangi hesaba kaydedilir?", "secenekler": ["191 İndirilecek KDV", "255 Demirbaşlar", "770 Genel Yönetim Gid."], "cevap": "191 İndirilecek KDV"},
    {"soru": "Çek keşide etmek (düzenleyip vermek) hangi hesabı alacaklandırır?", "secenekler": ["103 Verilen Çekler ve Ödeme Emirleri", "101 Alınan Çekler", "102 Bankalar"], "cevap": "103 Verilen Çekler ve Ödeme Emirleri"},
    {"soru": "Aşağıdakilerden hangisi Nazım Hesap niteliğindedir?", "secenekler": ["900 Borçlu Nazım Hesaplar", "100 Kasa", "500 Sermaye"], "cevap": "900 Borçlu Nazım Hesaplar"},
    {"soru": "İşletmenin 1 yıldan uzun vadeli borçları hangi ana grupta izlenir?", "secenekler": ["Uzun Vadeli Yabancı Kaynaklar", "Duran Varlıklar", "Özkaynaklar"], "cevap": "Uzun Vadeli Yabancı Kaynaklar"}
]

# --- OTURUM AYARLARI (SESSION STATE) ---
if 'oturum_basladi' not in st.session_state:
    st.session_state.oturum_basladi = False
if 'soru_listesi' not in st.session_state:
    st.session_state.soru_listesi = []
if 'mevcut_soru_index' not in st.session_state:
    st.session_state.mevcut_soru_index = 0
if 'puan' not in st.session_state:
    st.session_state.puan = 0
if 'dogru_sayisi' not in st.session_state:
    st.session_state.dogru_sayisi = 0
if 'yanlis_sayisi' not in st.session_state:
    st.session_state.yanlis_sayisi = 0
if 'sinav_bitti' not in st.session_state:
    st.session_state.sinav_bitti = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = {}

# --- FONKSİYONLAR ---
def sinavi_baslat(ad, soyad, sinif):
    st.session_state.user_info = {"ad": ad, "soyad": soyad, "sinif": sinif}
    # Havuzdan rastgele 10 soru seç
    st.session_state.soru_listesi = random.sample(tum_sorular, min(10, len(tum_sorular)))
    st.session_state.oturum_basladi = True
    st.session_state.sinav_bitti = False
    st.session_state.puan = 0
    st.session_state.mevcut_soru_index = 0
    st.rerun()

def cevap_ver(secilen, dogru_cevap):
    if secilen == dogru_cevap:
        st.session_state.puan += 10
        st.session_state.dogru_sayisi += 1
        st.toast("✅ Doğru Cevap! (+10 Puan)", icon="🎉")
    else:
        st.session_state.yanlis_sayisi += 1
        st.toast(f"❌ Yanlış! Doğrusu: {dogru_cevap}", icon="⚠️")
    
    time.sleep(1) # Cevabı görmesi için bekle
    
    if st.session_state.mevcut_soru_index + 1 < len(st.session_state.soru_listesi):
        st.session_state.mevcut_soru_index += 1
        st.rerun()
    else:
        st.session_state.sinav_bitti = True
        st.rerun()

def yeniden_baslat():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

# --- ANA UYGULAMA AKIŞI ---

# 1. GİRİŞ EKRANI
if not st.session_state.oturum_basladi:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135823.png", width=100)
    st.title("Bağarası ÇPAL | Finans Ligi")
    st.write("Muhasebe bilgini test et, skorunu yükselt!")
    
    with st.form("giris_formu"):
        ad = st.text_input("Adınız")
        soyad = st.text_input("Soyadınız")
        sinif = st.selectbox("Sınıfınız", ["9-A", "9-B", "10-A", "10-B", "11-A", "11-Muhasebe", "12-Muhasebe"])
        submit_btn = st.form_submit_button("Sınava Başla 🚀")
        
        if submit_btn:
            if ad and soyad:
                sinavi_baslat(ad, soyad, sinif)
            else:
                st.warning("Lütfen ad ve soyad alanlarını doldurun.")

# 2. SINAV EKRANI
elif not st.session_state.sinav_bitti:
    # İlerleme Çubuğu
    toplam_soru = len(st.session_state.soru_listesi)
    suanki = st.session_state.mevcut_soru_index + 1
    progress = st.session_state.mevcut_soru_index / toplam_soru
    
    st.progress(progress)
    st.caption(f"Soru {suanki} / {toplam_soru} | Oyuncu: {st.session_state.user_info['ad']} {st.session_state.user_info['soyad']}")
    
    # Soruyu Getir
    soru_verisi = st.session_state.soru_listesi[st.session_state.mevcut_soru_index]
    
    st.markdown(f"<div class='big-font'>{soru_verisi['soru']}</div>", unsafe_allow_html=True)
    st.write("") # Boşluk
    
    # Seçenekleri Karıştır (Ezberi önlemek için)
    secenekler = soru_verisi["secenekler"]
    # random.shuffle(secenekler) # İsterseniz seçenek yerlerini de karıştırabilirsiniz
    
    col1, col2, col3 = st.columns(3)
    
    # Butonları yan yana veya alt alta diz
    for i, secenek in enumerate(secenekler):
        if st.button(secenek, key=f"btn_{i}"):
            cevap_ver(secenek, soru_verisi["cevap"])

# 3. SONUÇ EKRANI (KARNE)
else:
    st.balloons()
    st.title("🏁 Sınav Tamamlandı!")
    
    skor = st.session_state.puan
    user = st.session_state.user_info
    
    # Karne Kartı
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"{user['ad']} {user['soyad']}")
        st.write(f"📂 Sınıf: {user['sinif']}")
    with col2:
        st.metric(label="TOPLAM PUAN", value=f"{skor} / 100")
    
    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.info(f"✅ Doğru: {st.session_state.dogru_sayisi}")
    c2.error(f"❌ Yanlış: {st.session_state.yanlis_sayisi}")
    
    # Başarı Mesajı
    if skor >= 80:
        st.success("🌟 MÜKEMMEL! Tam bir muhasebe uzmanısın.")
    elif skor >= 50:
        st.warning("👏 GÜZEL. Biraz daha tekrarla harika olabilir.")
    else:
        st.error("⚠️ DAHA ÇOK ÇALIŞMALISIN. Muhasebe defterlerini tekrar aç.")
        
    st.write("")
    if st.button("🔄 Yeni Sınav Başlat"):
        yeniden_baslat()
