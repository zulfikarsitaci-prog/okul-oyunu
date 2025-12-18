import streamlit as st
import google.generativeai as genai
import json
import time
import random
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Bağarası Çok Programlı Sınav Sistemi", page_icon="🏫", layout="centered")

# --- STİL (Okul Renkleri ve Düzen) ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; font-weight: bold; background-color: #f0f2f6; }
    .stButton>button:hover { background-color: #e0e2e6; color: #ff4b4b; border-color: #ff4b4b; }
    .big-font { font-size: 22px !important; font-weight: 600; color: #1f1f1f; }
    .header-text { color: #0e1117; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# --- DERS PROGRAMI MÜFREDATI ---
MUFREDAT = {
    "9. Sınıf": [
        "Temel Muhasebe", 
        "Mesleki Gelişim Atölyesi", 
        "Mesleki Matematik", 
        "Ofis Uygulamaları"
    ],
    "10. Sınıf": [
        "Finansal Muhasebe", 
        "Temel Hukuk", 
        "Temel Ekonomi", 
        "Klavye Teknikleri"
    ],
    "11. Sınıf": [
        "Maliyet Muhasebesi", 
        "Şirketler Muhasebesi", 
        "Bilgisayarlı Muhasebe (Luca)", 
        "Bilgisayarlı Muhasebe (ETA SQL)"
    ],
    "12. Sınıf": [
        "Bankacılık ve Finans", 
        "Finansal Okuryazarlık"
    ]
}

# --- YEDEK SORU DEPOSU (Yapay Zeka Çalışmazsa Buradan Çeker) ---
# Her ders için örnek sorular. Yapay zeka devredeyken burası kullanılmaz.
YEDEK_DEPO = {
    "Temel Muhasebe": [
        {"soru": "Tacir, işletmesiyle ilgili işlemleri kaydederken hangi kavrama uymalıdır?", "secenekler": ["Kişilik Kavramı", "Sosyal Sorumluluk", "Dönemsellik"], "cevap": "Kişilik Kavramı"},
        {"soru": "Varlık hesapları (Aktif) artış gösterdiğinde ne yapılır?", "secenekler": ["Borç kaydedilir", "Alacak kaydedilir", "Kapanır"], "cevap": "Borç kaydedilir"}
    ],
    "Mesleki Matematik": [
        {"soru": "Bir malın %18 KDV dahil fiyatı 1180 TL ise, KDV hariç fiyatı nedir?", "secenekler": ["1000 TL", "1100 TL", "900 TL"], "cevap": "1000 TL"},
        {"soru": "%20 karla 120 TL'ye satılan bir malın maliyeti kaç TL'dir?", "secenekler": ["100 TL", "90 TL", "110 TL"], "cevap": "100 TL"}
    ],
    "Ofis Uygulamaları": [
        {"soru": "Excel'de 'Eğer' formülü hangi mantıksal sınamayı yapar?", "secenekler": ["Koşul belirtir", "Toplama yapar", "Ortalama alır"], "cevap": "Koşul belirtir"},
        {"soru": "Word programında metni kalın yapmak için hangi kısayol kullanılır?", "secenekler": ["CTRL + K", "CTRL + C", "CTRL + V"], "cevap": "CTRL + K"}
    ],
    "Finansal Muhasebe": [
        {"soru": "Dönem sonu mal mevcudu hangi tabloda yer alır?", "secenekler": ["Bilanço ve Gelir Tablosu", "Sadece Bilanço", "Mizan"], "cevap": "Bilanço ve Gelir Tablosu"},
        {"soru": "102 Bankalar hesabı pasif karakterli midir?", "secenekler": ["Hayır, Aktiftir", "Evet, Pasiftir", "Nazım hesaptır"], "cevap": "Hayır, Aktiftir"}
    ],
    "Bilgisayarlı Muhasebe (Luca)": [
        {"soru": "Luca programında fiş kaydı ekranına girmek için hangi menü kullanılır?", "secenekler": ["Muhasebe > Fiş İşlemleri", "Personel > Bordro", "Yönetim"], "cevap": "Muhasebe > Fiş İşlemleri"},
        {"soru": "Luca'da KDV hesaplaması otomatik yapmak için hangi tuş kullanılır?", "secenekler": ["F9 veya Tanımlı Kısayol", "F1", "ESC"], "cevap": "F9 veya Tanımlı Kısayol"}
    ]
}

# --- YAPAY ZEKA BAĞLANTISI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def yapay_zeka_soru_uret(sinif, ders):
    ai_sorulari = []
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        # ÖĞRENCİYİ DÜŞÜNMEYE SEVK EDECEK GELİŞMİŞ PROMPT
        prompt = f"""
        Sen uzman bir Meslek Lisesi Öğretmenisin.
        Hedef Kitle: {sinif} öğrencisi.
        Ders Konusu: **{ders}**.
        
        Görevin: Bu ders için öğrencinin analiz yeteneğini ölçecek, ezberden uzak,
        gerçek hayat senaryoları veya teknik detaylar içeren 10 adet ÇOKTAN SEÇMELİ soru hazırla.
        
        Özel Talimatlar:
        - Eğer ders "Bilgisayarlı Muhasebe" ise program menüleri ve kısayolları sor.
        - Eğer ders "Hukuk" veya "Ekonomi" ise güncel kavramları sor.
        - Sorular ne çok basit ne de aşırı zor olsun, "Düşündürücü" olsun.
        
        ÇIKTI FORMATI (SADECE JSON):
        [
            {{ "soru": "Soru metni...", "secenekler": ["A şıkkı", "B şıkkı", "C şıkkı"], "cevap": "Doğru şıkkın metni" }}
        ]
        """
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        
        # JSON Temizliği
        if text_response.startswith("```"):
            text_response = text_response.split("```")[1]
            if text_response.startswith("json"):
                text_response = text_response[4:]
        
        ai_sorulari = json.loads(text_response)
    except Exception as e:
        # Hata olursa logla ama kullanıcıya yansıtma
        print(f"AI Hatası: {e}")
        ai_sorulari = []

    # EKSİK VARSA YEDEKTEN TAMAMLA
    # Not: Yedek depoda o ders yoksa genel muhasebe soruları eklenir
    if len(ai_sorulari) < 10:
        yedek_listesi = YEDEK_DEPO.get(ders, YEDEK_DEPO.get("Temel Muhasebe", []))
        eksik_sayi = 10 - len(ai_sorulari)
        if len(yedek_listesi) > 0:
            takviye = random.sample(yedek_listesi, min(eksik_sayi, len(yedek_listesi)))
            ai_sorulari.extend(takviye)
    
    return ai_sorulari[:10]

# --- GOOGLE SHEETS KAYIT SİSTEMİ ---
def sonuclari_kaydet(ad, soyad, sinif, ders, puan):
    try:
        if "gcp_service_account" in st.secrets:
            secrets_dict = st.secrets["gcp_service_account"]
            scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_info(secrets_dict, scopes=scope)
            client = gspread.authorize(creds)
            # Dosya adının 'Okul_Puanlari' olduğundan emin olun
            sheet = client.open("Okul_Puanlari").sheet1
            tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
            # Excel'e yazılacak satır: Tarih | Ad Soyad | Sınıf | Ders | Puan
            sheet.append_row([tarih, f"{ad} {soyad}", sinif, ders, puan])
            return True
        return False
    except Exception as e:
        st.error(f"Kayıt Hatası: {e}")
        return False

# --- EKRAN YÖNETİMİ (SESSION STATE) ---
if 'oturum_basladi' not in st.session_state: st.session_state.oturum_basladi = False
if 'soru_listesi' not in st.session_state: st.session_state.soru_listesi = []
if 'index' not in st.session_state: st.session_state.index = 0
if 'puan' not in st.session_state: st.session_state.puan = 0
if 'yukleniyor' not in st.session_state: st.session_state.yukleniyor = False
if 'kayit_ok' not in st.session_state: st.session_state.kayit_ok = False
if 'secilen_ders' not in st.session_state: st.session_state.secilen_ders = ""

# ==========================================
# 1. GİRİŞ EKRANI
# ==========================================
if not st.session_state.oturum_basladi:
    st.image("https://cdn-icons-png.flaticon.com/512/3609/3609741.png", width=100)
    st.markdown("<h1 class='header-text'>Bağarası ÇPAL Sınav Merkezi</h1>", unsafe_allow_html=True)
    st.info("Lütfen sınıfını ve sınav olmak istediğin dersi seç.")

    if st.session_state.yukleniyor:
        with st.status("Yapay Zeka Soruları Hazırlıyor...", expanded=True):
            st.write(f"Sınıf: {st.session_state.kimlik['sinif']}")
            st.write(f"Ders: {st.session_state.kimlik['ders']}")
            st.write("Gemini ile bağlantı kuruluyor...")
            
            # AI Soru Üretimi Çağrısı
            sorular = yapay_zeka_soru_uret(st.session_state.kimlik['sinif'], st.session_state.kimlik['ders'])
            
            st.session_state.soru_listesi = sorular
            st.session_state.oturum_basladi = True
            st.session_state.kayit_ok = False
            st.session_state.yukleniyor = False
            st.rerun()
    else:
        with st.form("giris_formu"):
            col1, col2 = st.columns(2)
            with col1:
                ad = st.text_input("Adınız")
            with col2:
                soyad = st.text_input("Soyadınız")
            
            # Sınıf Seçimi
            sinif_secimi = st.selectbox("Sınıfınız", list(MUFREDAT.keys()))
            
            # Seçilen sınıfa göre dersleri getir
            dersler_listesi = MUFREDAT[sinif_secimi]
            ders_secimi = st.selectbox("Hangi Dersten Sınav Olacaksın?", dersler_listesi)
            
            submit_btn = st.form_submit_button("Sınavı Başlat 🚀")
            
            if submit_btn:
                if ad and soyad:
                    st.session_state.kimlik = {
                        "ad": ad, 
                        "soyad": soyad, 
                        "sinif": sinif_secimi,
                        "ders": ders_secimi
                    }
                    st.session_state.puan = 0
                    st.session_state.index = 0
                    st.session_state.yukleniyor = True
                    st.rerun()
                else:
                    st.warning("Lütfen ad ve soyad giriniz.")

# ==========================================
# 2. SORU EKRANI
# ==========================================
elif st.session_state.index < len(st.session_state.soru_listesi):
    soru = st.session_state.soru_listesi[st.session_state.index]
    toplam_soru = len(st.session_state.soru_listesi)
    
    # İlerleme Çubuğu
    st.progress((st.session_state.index + 1) / toplam_soru)
    
    # Bilgi Çubuğu
    c1, c2 = st.columns([3, 1])
    c1.caption(f"Ders: {st.session_state.kimlik['ders']}")
    c2.caption(f"Soru {st.session_state.index + 1}/{toplam_soru}")
    
    # Soru Metni
    st.markdown(f"<div class='big-font'>{soru['soru']}</div>", unsafe_allow_html=True)
    st.write("") # Boşluk
    
    # Seçenekler
    secenekler = soru["secenekler"]
    # Şıkları karıştırmak isterseniz alttaki satırı açın
    # random.shuffle(secenekler)
    
    for sec in secenekler:
        if st.button(sec, use_container_width=True):
            if sec == soru["cevap"]:
                st.session_state.puan += 10
                st.toast("✅ Doğru! Harika gidiyorsun.", icon="🎉")
            else:
                st.toast(f"❌ Yanlış! Doğru cevap: {soru['cevap']}", icon="⚠️")
            
            time.sleep(1.5) # Cevabı okuması için süre
            st.session_state.index += 1
            st.rerun()

# ==========================================
# 3. SONUÇ EKRANI
# ==========================================
else:
    st.balloons()
    st.success("Sınav Tamamlandı!")
    
    # Karne Alanı
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    col1.metric("Öğrenci", f"{st.session_state.kimlik['ad']}")
    col2.metric("Ders", f"{st.session_state.kimlik['ders']}")
    col3.metric("PUAN", f"{st.session_state.puan}")
    st.markdown("---")
    
    # Otomatik Kayıt
    if not st.session_state.kayit_ok:
        with st.spinner("Sonuç sisteme işleniyor..."):
            sonuc = sonuclari_kaydet(
                st.session_state.kimlik["ad"],
                st.session_state.kimlik["soyad"],
                st.session_state.kimlik["sinif"],
                st.session_state.kimlik["ders"],
                st.session_state.puan
            )
            if sonuc:
                st.success("✅ Sonuç Öğretmenine Başarıyla İletildi.")
                st.session_state.kayit_ok = True
            else:
                st.error("⚠️ Kayıt sırasında hata oluştu. Lütfen ekran görüntüsü al.")

    # Yorum
    if st.session_state.puan >= 80:
        st.write("🌟 **Mükemmel!** Bu konuya hakimsin.")
    elif st.session_state.puan >= 50:
        st.write("👍 **Güzel.** Biraz daha tekrarla harika olur.")
    else:
        st.write("📚 **Dikkat.** Konu tekrarı yapman gerekebilir.")

    if st.button("Ana Menüye Dön / Yeni Sınav"):
        st.session_state.oturum_basladi = False
        st.rerun()
