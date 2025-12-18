import streamlit as st
import google.generativeai as genai
import json
import time
import random
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Bağarası ÇPAL Sınav Merkezi", page_icon="🏫", layout="centered")

# --- GÖRÜNTÜ AYARLARI (Beyaz Ekran & Okunaklı Yazılar) ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    h1, h2, h3, h4, h5, h6, p, div, span, label, li { color: #000000 !important; }
    .stButton>button { 
        width: 100%; border-radius: 10px; min-height: 4em; 
        font-weight: 500; background-color: #f8f9fa !important; 
        color: #000000 !important; border: 2px solid #e9ecef !important;
        white-space: pre-wrap; text-align: left !important; padding-left: 20px;
    }
    .stButton>button:hover { background-color: #e2e6ea !important; border-color: #adb5bd !important; }
    .big-font { font-size: 22px !important; font-weight: 700; color: #111827 !important; margin-bottom: 25px; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #ffffff !important; color: #000000 !important; border-color: #ced4da !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- MÜFREDAT VE KONU HAVUZU (YILLIK PLANLARDAN ÇEKİLENLER) ---
# Buradaki konular sizin excel dosyalarınızdan alınmıştır.
KONU_HAVUZU = {
    # ---------------- 9. SINIF ----------------
    "Temel Muhasebe": [
        "Fatura ve İrsaliye Düzenleme", "Perakende Satış Fişi ve Yazar Kasa", "Gider Pusulası ve Müstahsil Makbuzu",
        "Serbest Meslek Makbuzu", "Ticari Defterler ve Tasdik Zamanları", "İşletme Hesabı Defteri Gider Kayıtları",
        "İşletme Hesabı Defteri Gelir Kayıtları", "Vergi Dairesi ve Belediye İşlemleri", "SGK İşe Giriş Bildirgesi"
    ],
    "Mesleki Matematik": [
        "Yüzde Hesaplamaları", "Binde Hesaplamaları", "Alış, Maliyet, Satış ve Kar Hesapları",
        "KDV Hesaplamaları (Hariç/Dahil)", "Ticari Belgelerde Tutar Hesaplama", "Oran ve Orantı",
        "Basit İskonto Hesaplamaları", "Karışım ve Alaşım Problemleri", "Faiz Hesaplamaları"
    ],
    "Ofis Uygulamaları": [
        "F Klavye Tuş Dizilimi", "Word'de Metin Biçimlendirme", "Word'de Tablo Oluşturma",
        "Excel'de Hücre ve Sayfa Yapısı", "Excel Formülleri (Topla, Ortalama, Eğer)", "Excel'de Grafik Oluşturma",
        "PowerPoint Slayt Tasarımı", "PowerPoint Geçiş ve Animasyonlar", "Yazıcı ve Çıktı Ayarları"
    ],
    "Mesleki Gelişim Atölyesi": [
        "Ahilik Kültürü ve Meslek Etiği", "İletişim Süreci ve Türleri", "İş Sağlığı ve Güvenliği Tedbirleri",
        "Girişimcilik Fikirleri", "Proje Hazırlama Süreçleri", "Çevre Koruma ve Atık Yönetimi",
        "Teknolojik Gelişmeler ve Meslekler", "Kişisel Gelişim ve Kariyer Planlama"
    ],

    # ---------------- 10. SINIF ----------------
    "Finansal Muhasebe": [
        "Bilanço Eşitliği ve Temel Kavramlar", "Varlık Hesaplarının İşleyişi (Kasa, Banka, Çek)", 
        "Kaynak Hesaplarının İşleyişi (Satıcılar, Krediler)", "Yevmiye Defteri Kayıt Kuralları", 
        "Büyük Defter (Defter-i Kebir) Aktarımı", "Mizan Düzenleme (Geçici ve Kesin Mizan)",
        "Gelir Tablosu Hesapları (600, 770 vb.)", "KDV Tahakkuk Kayıtları", "Dönem Sonu Envanter İşlemleri"
    ],
    "Temel Hukuk": [
        "Hukukun Temel Kaynakları", "Hak Kavramı ve Hak Ehliyeti", "Kişiler Hukuku (Gerçek ve Tüzel Kişiler)",
        "Borçlar Hukuku ve Sözleşmeler", "Aile ve Miras Hukuku", "Mülkiyet Hakkı", 
        "Yargı Organları ve Dava Türleri", "Sigorta Hukuku (Can ve Mal Sigortaları)"
    ],
    "Temel Ekonomi": [
        "Ekonominin Temel Kavramları (İhtiyaç, Fayda)", "Üretim Faktörleri", "Arz ve Talep Kanunu",
        "Piyasa Çeşitleri ve Fiyat Oluşumu", "Enflasyon ve Deflasyon", "Para ve Bankacılık",
        "Milli Gelir Kavramları", "Dış Ticaret ve Döviz Kurları"
    ],
    "Klavye Teknikleri": [
        "F Klavye Temel Sıra Tuşları", "Üst ve Alt Sıra Tuşları", "Rakam ve Sembol Tuşları",
        "Oturuş ve Duruş Teknikleri", "Süreli Metin Yazma Çalışmaları", "Hatasız Yazma Teknikleri"
    ],

    # ---------------- 11. SINIF ----------------
    "Bilgisayarlı Muhasebe": [
        "Şirket/Firma Tanımlama İşlemleri", "Stok Kartı ve Cari Kart Açma", "Alış ve Satış Faturası İşleme",
        "Muhasebe Fişleri (Tahsil, Tediye, Mahsup)", "Çek ve Senet Modülü İşlemleri", "Banka Hareketleri Kaydı",
        "Kasa İşlemleri", "KDV Beyannamesi Hazırlama", "Dönem Sonu Devir İşlemleri"
    ],
    "Maliyet Muhasebesi": [
        "Maliyet, Gider ve Harcama Kavramları", "7A ve 7B Maliyet Seçenekleri", 
        "Direkt İlk Madde ve Malzeme Giderleri (150)", "Direkt İşçilik Giderleri (720)", 
        "Genel Üretim Giderleri (730)", "Maliyet Dağıtım Yöntemleri", "Satılan Mamul Maliyeti Tablosu",
        "Hizmet Üretim Maliyeti"
    ],
    "Şirketler Muhasebesi": [
        "Şirket Türleri ve Özellikleri", "Şirket Kuruluş Kayıtları", "Sermaye Artırımı İşlemleri",
        "Sermaye Azaltımı İşlemleri", "Kar Dağıtımı ve Yedek Akçeler", "Şirketlerde Tasfiye Süreci",
        "Şirket Birleşmeleri ve Devir", "Anonim Şirketlerde Hisse Senedi İşlemleri"
    ],
    "Vergi ve Beyannameler": [
        "Vergi Usul Kanunu Temel Hükümler", "Gelir Vergisi ve Unsurları", "Kurumlar Vergisi",
        "Katma Değer Vergisi (KDV)", "Özel Tüketim Vergisi (ÖTV)", "Motorlu Taşıtlar Vergisi (MTV)",
        "Muhtasar ve Prim Hizmet Beyannamesi", "Geçici Vergi Beyannamesi"
    ],
    "İş ve Sosyal Güvenlik": [
        "İş Kanunu ve İş Sözleşmeleri", "Ücret ve Ücret Bordrosu", "Kıdem ve İhbar Tazminatı",
        "Yıllık İzin ve Çalışma Saatleri", "İş Sağlığı ve Güvenliği Mevzuatı", "Sosyal Sigortalar ve GSS",
        "Sendikalar ve Toplu İş Sözleşmesi"
    ],
    "Girişimcilik": [
        "Girişimcilik Türleri", "İş Planı Hazırlama (Business Plan)", "Fizibilite Çalışması",
        "Pazar Araştırması", "Pazarlama Stratejileri", "Yenilikçilik (İnovasyon)", "KOSGEB Destekleri"
    ],

    # ---------------- 12. SINIF ----------------
    "Dış Ticaret": [
        "Dış Ticaret Rejimi ve Mevzuatı", "İhracat ve İthalat Kavramları", "Dış Ticarette Ödeme Şekilleri",
        "Teslim Şekilleri (Incoterms - FOB, CIF vb.)", "Gümrük İşlemleri ve Belgeler", 
        "Kambiyo Mevzuatı", "Serbest Bölgeler", "Dış Ticarette Finansman"
    ],
    "Kooperatifçilik": [
        "Kooperatifçilik İlkeleri", "Kooperatif Kuruluş İşlemleri", "Ana Sözleşme Hazırlama",
        "Ortaklık Hak ve Ödevleri", "Kooperatif Organları (Genel Kurul, Yönetim)", 
        "Kooperatiflerde Gelir-Gider Dağılımı", "Kooperatiflerde Tasfiye"
    ],
    "Hızlı Klavye": [
        "İleri Seviye Metin Yazma", "Hukuki ve Adli Metin Yazımı", "Dikte Çalışmaları", 
        "Rapor ve Tutanak Düzenleme", "Yazışma Kuralları"
    ]
}

# --- DERS LİSTESİ OLUŞTURMA ---
MUFREDAT = {
    "9. Sınıf": ["Temel Muhasebe", "Mesleki Matematik", "Ofis Uygulamaları", "Mesleki Gelişim Atölyesi"],
    "10. Sınıf": ["Finansal Muhasebe", "Temel Hukuk", "Temel Ekonomi", "Klavye Teknikleri"],
    "11. Sınıf": ["Bilgisayarlı Muhasebe", "Maliyet Muhasebesi", "Şirketler Muhasebesi", "Vergi ve Beyannameler", "İş ve Sosyal Güvenlik", "Girişimcilik"],
    "12. Sınıf": ["Dış Ticaret", "Kooperatifçilik", "Hızlı Klavye"]
}

# --- YEDEK SORU DEPOSU (ACİL DURUM İÇİN) ---
YEDEK_DEPO = {
    "Genel": [
        {"soru": "Bilanço eşitliği aşağıdakilerden hangisidir?", "secenekler": ["Varlıklar = Kaynaklar", "Gelir = Gider", "Borç = Alacak", "Kasa = Banka", "Aktif = Gelir"], "cevap": "Varlıklar = Kaynaklar"},
        {"soru": "KDV hariç 1000 TL olan malın %20 KDV dahil tutarı nedir?", "secenekler": ["1200 TL", "1020 TL", "1180 TL", "1100 TL", "1250 TL"], "cevap": "1200 TL"},
        {"soru": "Excel'de toplama işlemi yapan formül hangisidir?", "secenekler": ["=TOPLA()", "=ÇIKAR()", "=ORTALAMA()", "=EĞER()", "=SAY()"], "cevap": "=TOPLA()"}
    ]
}

# --- AI AYARLARI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def yapay_zeka_soru_uret(sinif, ders):
    ai_sorulari = []
    
    # 1. KONU SEÇİMİ (HAVUZDAN RASTGELE ÇEK)
    konu_listesi = KONU_HAVUZU.get(ders, ["Genel Muhasebe Konuları"])
    secilen_konular = ", ".join(random.sample(konu_listesi, min(3, len(konu_listesi))))
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Rolün: Meslek Lisesi Öğretmeni.
        Ders: {ders} (Sınıf: {sinif}).
        
        Aşağıdaki Yıllık Plan Konularından 10 ADET soru hazırla:
        KONULAR: {secilen_konular}
        
        KURALLAR:
        1. Sorular 5 şıklı (A,B,C,D,E) olsun.
        2. Cevaplar şıklara rastgele dağılsın (Hepsi A olmasın).
        3. Sorular güncel mevzuata (2025) uygun olsun.
        4. Çıktı SADECE JSON formatında olsun.
        
        JSON FORMATI:
        [ {{ "soru": "...", "secenekler": ["A", "B", "C", "D", "E"], "cevap": "..." }} ]
        """
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        
        if text_response.startswith("```"):
            text_response = text_response.split("```")[1]
            if text_response.startswith("json"):
                text_response = text_response[4:]
        
        ai_sorulari = json.loads(text_response)
        
    except Exception as e:
        ai_sorulari = []

    # 2. YEDEKLEME (Eksik gelirse)
    if len(ai_sorulari) < 10:
        yedek = YEDEK_DEPO["Genel"]
        eksik = 10 - len(ai_sorulari)
        ai_sorulari.extend(random.choices(yedek, k=eksik))
            
    # 3. KARIŞTIRMA
    for soru in ai_sorulari:
        random.shuffle(soru["secenekler"])
    
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

# GİRİŞ EKRANI
if not st.session_state.oturum_basladi:
    st.markdown("<h1 style='text-align: center;'>Bağarası ÇPAL Sınav Merkezi</h1>", unsafe_allow_html=True)
    
    st.write("### 1. Ders Seçimi")
    secilen_sinif = st.selectbox("Sınıfınız:", list(MUFREDAT.keys()))
    dersler = MUFREDAT[secilen_sinif]
    secilen_ders = st.selectbox("Ders Seçiniz:", dersler)
    
    st.write("### 2. Öğrenci Bilgileri")
    with st.form("giris_formu"):
        col1, col2 = st.columns(2)
        ad = col1.text_input("Adınız")
        soyad = col2.text_input("Soyadınız")
        btn = st.form_submit_button("Sınavı Başlat 🚀")
        
        if btn:
            if ad and soyad:
                st.session_state.kimlik = {"ad": ad, "soyad": soyad, "sinif": secilen_sinif, "ders": secilen_ders}
                st.session_state.yukleniyor = True
                st.rerun()
            else:
                st.warning("Ad ve Soyad zorunludur.")

    if st.session_state.yukleniyor:
        with st.status(f"Yıllık Plandan Sorular Çekiliyor... ({st.session_state.kimlik['ders']})", expanded=True):
            sorular = yapay_zeka_soru_uret(st.session_state.kimlik['sinif'], st.session_state.kimlik['ders'])
            
            if not sorular: 
                sorular = YEDEK_DEPO["Genel"]
                
            st.session_state.soru_listesi = sorular
            st.session_state.oturum_basladi = True
            st.session_state.yukleniyor = False
            st.rerun()

# SORU EKRANI
elif st.session_state.index < len(st.session_state.soru_listesi):
    soru = st.session_state.soru_listesi[st.session_state.index]
    toplam = len(st.session_state.soru_listesi)
    
    st.progress((st.session_state.index + 1) / toplam)
    st.markdown(f"**{st.session_state.kimlik['ders']}** | Soru {st.session_state.index + 1} / {toplam}")
    
    st.markdown(f"<div class='big-font'>{soru['soru']}</div>", unsafe_allow_html=True)
    
    for sec in soru["secenekler"]:
        if st.button(sec, use_container_width=True):
            if sec == soru["cevap"]:
                st.session_state.puan += 10
                st.toast("✅ Doğru!", icon="🎉")
            else:
                st.toast(f"❌ Yanlış! Cevap: {soru['cevap']}", icon="⚠️")
            time.sleep(1.5)
            st.session_state.index += 1
            st.rerun()

# SONUÇ EKRANI
else:
    st.balloons()
    st.success("Sınav Tamamlandı!")
    
    st.markdown(f"""
    <div style='background-color:#f0f2f6; padding:20px; border-radius:10px; text-align:center;'>
        <h2>{st.session_state.kimlik['ad']} {st.session_state.kimlik['soyad']}</h2>
        <h3>Puan: {st.session_state.puan}</h3>
        <p>{st.session_state.kimlik['sinif']} - {st.session_state.kimlik['ders']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.kayit_ok:
        with st.spinner("Sonuç kaydediliyor..."):
            res = sonuclari_kaydet(
                st.session_state.kimlik["ad"], st.session_state.kimlik["soyad"],
                st.session_state.kimlik["sinif"], st.session_state.kimlik["ders"],
                st.session_state.puan
            )
            if res:
                st.success("Kayıt Başarılı ✅")
                st.session_state.kayit_ok = True
    
    if st.button("Çıkış Yap"):
        st.session_state.oturum_basladi = False
        st.rerun()
