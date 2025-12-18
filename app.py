import streamlit as st
import google.generativeai as genai
import json
import time
import random
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Bağarası ÇPAL Sınav Merkezi", page_icon="📝", layout="centered")

# --- GÖRÜNTÜ AYARLARI (SARI ZEMİN - SİYAH YAZI) ---
st.markdown("""
    <style>
    .stApp { background-color: #FFF9C4 !important; }
    h1, h2, h3, h4, h5, h6, p, div, span, label, li, .stMarkdown { color: #000000 !important; }
    .stButton>button { 
        width: 100%; border-radius: 10px; min-height: 4em; font-weight: 600; 
        background-color: #FFEB3B !important; color: #000000 !important; 
        border: 2px solid #FBC02D !important; text-align: left !important; padding-left: 20px;
    }
    .stButton>button:hover { background-color: #FDD835 !important; border-color: #000000 !important; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important; color: #000000 !important; border: 2px solid #000000 !important;
    }
    .big-font { font-size: 22px !important; font-weight: 800; color: #000000 !important; margin-bottom: 25px; }
    </style>
""", unsafe_allow_html=True)

# --- 1. MÜFREDAT LİSTESİ ---
MUFREDAT = {
    "9. Sınıf": ["Temel Muhasebe", "Mesleki Matematik", "Ofis Uygulamaları", "Mesleki Gelişim Atölyesi"],
    "10. Sınıf": ["Genel Muhasebe", "Temel Hukuk", "Ekonomi", "Klavye Teknikleri"],
    "11. Sınıf": ["Bilgisayarlı Muhasebe", "Maliyet Muhasebesi", "Şirketler Muhasebesi", "Vergi ve Beyannameler", "İş ve Sosyal Güvenlik Hukuku", "Girişimcilik"],
    "12. Sınıf": ["Dış Ticaret", "Kooperatifçilik", "Hızlı Klavye", "Ahilik Kültürü"]
}

# --- 2. KONU HAVUZU (YILLIK PLANLARDAN ÇEKİLEN GERÇEK KONULAR) ---
KONU_HAVUZU = {
    "Temel Muhasebe": ["Fatura ve İrsaliye", "Perakende Satış Fişi", "Gider Pusulası", "İşletme Defteri Gider/Gelir Kaydı", "KDV Hesaplama", "Vergi Dairesi İşlemleri"],
    "Mesleki Matematik": ["Yüzde Hesapları", "Maliyet ve Satış Fiyatı", "İskonto Hesapları", "KDV Dahil/Hariç Hesaplama", "Kar/Zarar Problemleri", "Basit Faiz"],
    "Ofis Uygulamaları": ["Word Biçimlendirme", "Excel Formülleri (Topla, Ortalama, Eğer)", "PowerPoint Slayt Tasarımı", "Donanım Birimleri"],
    "Mesleki Gelişim Atölyesi": ["Ahilik ve Meslek Etiği", "İletişim Türleri", "İş Sağlığı ve Güvenliği", "Girişimcilik Fikirleri", "Proje Hazırlama"],
    
    "Genel Muhasebe": ["Bilanço İlkeleri", "Tek Düzen Hesap Planı", "Yevmiye Kayıtları", "Büyük Defter", "Mizan", "Nazım Hesaplar", "Dönem Sonu İşlemleri"],
    "Temel Hukuk": ["Hukukun Kaynakları", "Hak ve Ehliyet", "Borçlar Hukuku", "Sözleşme Türleri", "Ticaret Hukuku (Tacir)", "Kıymetli Evrak (Çek, Senet)", "Sigorta Hukuku"],
    "Ekonomi": ["Arz ve Talep", "Piyasa Dengesi", "Enflasyon", "Merkez Bankası", "Milli Gelir", "Dış Ticaret Dengesi", "Uluslararası Kuruluşlar"],
    "Klavye Teknikleri": ["F Klavye Tuş Dizilimi", "Oturuş Tekniği", "Süreli Metin Yazma", "Rakam ve Sembol Tuşları"],
    
    "Bilgisayarlı Muhasebe": ["Şirket Açma", "Stok ve Cari Kart", "Fatura İşleme", "Muhasebe Fişleri (Tahsil/Tediye/Mahsup)", "Çek/Senet Modülü", "Entegrasyon"],
    "Maliyet Muhasebesi": ["7A ve 7B Seçenekleri", "Direkt İlk Madde Giderleri (150)", "Direkt İşçilik (720)", "Genel Üretim Giderleri (730)", "Satılan Mamul Maliyeti"],
    "Şirketler Muhasebesi": ["Şirket Kuruluş Kayıtları", "Sermaye Artırımı/Azaltımı", "Kar Dağıtımı", "Şirket Birleşmeleri", "Tasfiye İşlemleri"],
    "Vergi ve Beyannameler": ["KDV Beyannamesi", "Muhtasar Beyanname", "Geçici Vergi", "Gelir ve Kurumlar Vergisi", "ÖTV ve MTV"],
    "İş ve Sosyal Güvenlik Hukuku": ["İş Sözleşmesi Türleri", "Kıdem ve İhbar Tazminatı", "Ücret Bordrosu", "İş Kazası ve Meslek Hastalığı", "Sendikalar"],
    "Girişimcilik": ["İş Planı Hazırlama", "Fizibilite Raporu", "SWOT Analizi", "Pazarlama Stratejileri", "KOSGEB Destekleri"],
    
    "Dış Ticaret": ["İhracat ve İthalat", "Teslim Şekilleri (Incoterms)", "Ödeme Şekilleri (Akreditif vb.)", "Gümrük İşlemleri", "Kambiyo Mevzuatı"],
    "Kooperatifçilik": ["Kooperatif İlkeleri", "Kuruluş İşlemleri", "Ortaklık Hakları", "Risturn Dağıtımı", "Genel Kurul"],
    "Hızlı Klavye": ["Adli Metin Yazımı", "Zabıt Kâtipliği Metinleri", "Dikte Çalışmaları"],
    "Ahilik Kültürü": ["Ahilik Teşkilatı", "Fütüvvetname", "Usta-Çırak İlişkisi", "Meslek Ahlakı"]
}

# --- 3. GENİŞLETİLMİŞ YEDEK SORU DEPOSU (AI ÇALIŞMAZSA DEVREYE GİRER) ---
YEDEK_DEPO = {
    "Temel Hukuk": [
        {"soru": "Hak ehliyeti ne zaman başlar?", "secenekler": ["Tam ve sağ doğumla", "18 yaşla", "Evlenince", "Okula başlayınca", "İşe girince"], "cevap": "Tam ve sağ doğumla"},
        {"soru": "Borcun unsurları nelerdir?", "secenekler": ["Alacaklı, Borçlu, Edim", "Hakim, Savcı, Avukat", "Para, Mal, Hizmet", "Yasa, Tüzük, Yönetmelik", "Davacı, Davalı, Tanık"], "cevap": "Alacaklı, Borçlu, Edim"},
        {"soru": "Çek üzerindeki vadeye ne ad verilir?", "secenekler": ["Keşide Tarihi", "Vade", "Tanzim", "Ciro", "Aval"], "cevap": "Keşide Tarihi"},
        {"soru": "Tacir kime denir?", "secenekler": ["Ticari işletmeyi işleten kişi", "Devlet memuru", "Tüketici", "Öğrenci", "Dernek başkanı"], "cevap": "Ticari işletmeyi işleten kişi"}
    ],
    "Genel Muhasebe": [
        {"soru": "Bilanço denkliği hangisidir?", "secenekler": ["Varlıklar = Kaynaklar", "Gelir = Gider", "Aktif = Pasif - Sermaye", "Kasa = Banka", "Borç = Alacak"], "cevap": "Varlıklar = Kaynaklar"},
        {"soru": "100 Kasa hesabı nasıl çalışır?", "secenekler": ["Girişler Borç, Çıkışlar Alacak", "Girişler Alacak, Çıkışlar Borç", "Hep Alacaklı", "Hep Borçlu", "Çalışmaz"], "cevap": "Girişler Borç, Çıkışlar Alacak"},
        {"soru": "Satıcıya borçlandığımızda hangi hesap kullanılır?", "secenekler": ["320 Satıcılar", "120 Alıcılar", "102 Bankalar", "600 Satışlar", "500 Sermaye"], "cevap": "320 Satıcılar"},
        {"soru": "Tek düzen hesap planında 6 ile başlayan hesaplar nedir?", "secenekler": ["Gelir Tablosu Hesapları", "Varlık Hesapları", "Kaynak Hesapları", "Maliyet Hesapları", "Nazım Hesaplar"], "cevap": "Gelir Tablosu Hesapları"}
    ],
    "Ofis Uygulamaları": [
        {"soru": "Excel'de toplama formülü nedir?", "secenekler": ["=TOPLA()", "=ÇIKAR()", "=SAY()", "=EĞER()", "=ORTALAMA()"], "cevap": "=TOPLA()"},
        {"soru": "Word'de kaydetme kısayolu nedir?", "secenekler": ["CTRL+S", "CTRL+C", "CTRL+V", "CTRL+P", "CTRL+Z"], "cevap": "CTRL+S"},
        {"soru": "Sunum hazırlama programı hangisidir?", "secenekler": ["PowerPoint", "Excel", "Word", "Access", "Outlook"], "cevap": "PowerPoint"}
    ],
    "Maliyet Muhasebesi": [
        {"soru": "Direkt İlk Madde ve Malzeme Giderleri hangi hesapta izlenir?", "secenekler": ["150", "720", "730", "770", "600"], "cevap": "150"},
        {"soru": "Üretimle doğrudan ilişkisi kurulamayan giderler hangisidir?", "secenekler": ["Genel Üretim Giderleri", "Direkt İşçilik", "Direkt Malzeme", "Pazarlama Gideri", "Finansman Gideri"], "cevap": "Genel Üretim Giderleri"}
    ],
    "Vergi ve Beyannameler": [
        {"soru": "KDV beyannamesi ne zaman verilir?", "secenekler": ["Takip eden ayın 28'i", "Yıl sonunda", "Her hafta", "Günlük", "3 ayda bir"], "cevap": "Takip eden ayın 28'i"},
        {"soru": "Motorlu Taşıtlar Vergisi (MTV) yılda kaç taksittir?", "secenekler": ["2 Taksit (Ocak-Temmuz)", "Tek seferde", "12 Taksit", "4 Taksit", "Ödenmez"], "cevap": "2 Taksit (Ocak-Temmuz)"}
    ],
    "Genel": [
        {"soru": "İşletmenin en likit varlığı nedir?", "secenekler": ["Kasa", "Bina", "Demirbaş", "Taşıt", "Arsa"], "cevap": "Kasa"},
        {"soru": "Hangisi bir finansal tablodur?", "secenekler": ["Bilanço", "Fatura", "İrsaliye", "Çek", "Senet"], "cevap": "Bilanço"}
    ]
}

# --- AI AYARLARI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def yapay_zeka_soru_uret(sinif, ders):
    ai_sorulari = []
    konu_listesi = KONU_HAVUZU.get(ders, ["Genel Konular"])
    # Rastgele 3 konu seç
    secilen_konular = random.sample(konu_listesi, min(3, len(konu_listesi)))
    konu_metni = ", ".join(secilen_konular)
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        # Daha fazla soru isteyip içinden 10 tanesini alacağız (Garanti olsun diye)
        prompt = f"""
        Rolün: Öğretmen. Ders: {ders} ({sinif}).
        Konular: {konu_metni}.
        
        GÖREV: Bu konulardan 12 adet test sorusu üret.
        
        KURALLAR:
        1. Sorular dersin içeriğiyle TAM UYUMLU olsun. (Örn: Hukuk dersinde muhasebe sorma).
        2. Her sorunun 5 şıkkı (A,B,C,D,E) olsun.
        3. Cevaplar rastgele şıklara dağılsın.
        4. Çıktı SADECE JSON olsun.
        
        JSON: [ {{ "soru": "...", "secenekler": ["..."], "cevap": "..." }} ]
        """
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        if text_response.startswith("```"):
            text_response = text_response.split("```")[1].strip()
        if text_response.startswith("json"):
            text_response = text_response[4:].strip()
            
        ai_sorulari = json.loads(text_response)
    except:
        ai_sorulari = []

    # EKSİK KALIRSA YEDEKTEN TAMAMLA
    if len(ai_sorulari) < 10:
        # Önce derse özel yedeği bul
        ozel_yedek = YEDEK_DEPO.get(ders, [])
        if not ozel_yedek:
            # Bulamazsa genelden veya en yakın dersten tamamla
            if "Muhasebe" in ders: ozel_yedek = YEDEK_DEPO["Genel Muhasebe"]
            elif "Hukuk" in ders: ozel_yedek = YEDEK_DEPO["Temel Hukuk"]
            else: ozel_yedek = YEDEK_DEPO["Genel"]
            
        eksik = 10 - len(ai_sorulari)
        # Yedekleri karıştırıp ekle
        random.shuffle(ozel_yedek)
        ai_sorulari.extend(ozel_yedek[:eksik])
            
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

if not st.session_state.oturum_basladi:
    st.markdown("<h1 style='text-align: center;'>Bağarası ÇPAL Sınav Merkezi</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        secilen_sinif = st.selectbox("Sınıfınız:", list(MUFREDAT.keys()))
    with col2:
        secilen_ders = st.selectbox("Ders Seçiniz:", MUFREDAT[secilen_sinif])
    
    with st.form("giris"):
        st.write("### Öğrenci Bilgileri")
        c1, c2 = st.columns(2)
        ad = c1.text_input("Ad")
        soyad = c2.text_input("Soyad")
        if st.form_submit_button("BAŞLA 🚀"):
            if ad and soyad:
                st.session_state.kimlik = {"ad": ad, "soyad": soyad, "sinif": secilen_sinif, "ders": secilen_ders}
                st.session_state.yukleniyor = True
                st.rerun()

    if st.session_state.yukleniyor:
        with st.status("Sorular Hazırlanıyor...", expanded=True):
            sorular = yapay_zeka_soru_uret(st.session_state.kimlik['sinif'], st.session_state.kimlik['ders'])
            st.session_state.soru_listesi = sorular
            st.session_state.oturum_basladi = True
            st.session_state.yukleniyor = False
            st.rerun()

elif st.session_state.index < len(st.session_state.soru_listesi):
    soru = st.session_state.soru_listesi[st.session_state.index]
    toplam = len(st.session_state.soru_listesi)
    st.progress((st.session_state.index + 1) / toplam)
    st.write(f"**{st.session_state.kimlik['ders']}** - Soru {st.session_state.index + 1}/{toplam}")
    st.markdown(f"<div class='big-font'>{soru['soru']}</div>", unsafe_allow_html=True)
    
    for sec in soru["secenekler"]:
        if st.button(sec, use_container_width=True):
            if sec == soru["cevap"]:
                st.session_state.puan += 10
                st.toast("✅ Doğru!", icon="🎉")
            else:
                st.toast(f"❌ Yanlış! Cevap: {soru['cevap']}", icon="⚠️")
            time.sleep(1)
            st.session_state.index += 1
            st.rerun()
else:
    st.balloons()
    st.success("Sınav Bitti!")
    st.markdown(f"""
    <div style='background-color:#FFEB3B; padding:20px; border-radius:10px; text-align:center; border:2px solid black;'>
        <h2>{st.session_state.kimlik['ad']} {st.session_state.kimlik['soyad']}</h2>
        <h1>PUAN: {st.session_state.puan}</h1>
        <p>{st.session_state.kimlik['ders']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.kayit_ok:
        if sonuclari_kaydet(st.session_state.kimlik["ad"], st.session_state.kimlik["soyad"], st.session_state.kimlik["sinif"], st.session_state.kimlik["ders"], st.session_state.puan):
            st.success("Kayıt Başarılı ✅")
            st.session_state.kayit_ok = True
            
    if st.button("Çıkış"):
        st.session_state.oturum_basladi = False
        st.rerun()
