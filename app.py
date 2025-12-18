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
    .big-font { font-size: 20px !important; font-weight: 800; color: #000000 !important; margin-bottom: 25px; padding: 10px; border-left: 5px solid black; background: rgba(255,255,255,0.5); }
    </style>
""", unsafe_allow_html=True)

# --- 1. MÜFREDAT LİSTESİ ---
MUFREDAT = {
    "9. Sınıf": ["Temel Muhasebe", "Mesleki Matematik", "Ofis Uygulamaları", "Mesleki Gelişim Atölyesi"],
    "10. Sınıf": ["Genel Muhasebe", "Temel Hukuk", "Ekonomi", "Klavye Teknikleri"],
    "11. Sınıf": ["Bilgisayarlı Muhasebe", "Maliyet Muhasebesi", "Şirketler Muhasebesi", "Vergi ve Beyannameler", "İş ve Sosyal Güvenlik Hukuku", "Girişimcilik ve İşletme"],
    "12. Sınıf": ["Dış Ticaret", "Kooperatifçilik", "Hızlı Klavye", "Ahilik Kültürü ve Girişimcilik"]
}

# --- 2. KONU HAVUZU (DOSYALARINIZDAN ÇEKİLEN GERÇEK KONULAR) ---
KONU_HAVUZU = {
    "9-Temel Muhasebe": "Ticari Defterler, Fatura, İrsaliye, Perakende Satış Fişi, Gider Pusulası, Müstahsil Makbuzu, Serbest Meslek Makbuzu, İşletme Defteri Gider/Gelir.",
    "9-Mesleki Matematik": "Yüzde ve Binde Hesapları, Maliyet ve Satış Fiyatı, KDV Hesaplamaları, İskonto, Karışım Problemleri, Oran-Orantı.",
    "9-Ofis Uygulamaları": "Word Biçimlendirme, Excel Formülleri (Topla, Ortalama, Eğer), PowerPoint Tasarımı, Donanım Birimleri.",
    "9-Mesleki Gelişim Atölyesi": "Ahilik Kültürü, Meslek Etiği, İletişim Türleri, İş Sağlığı ve Güvenliği, Proje Hazırlama.",
    
    "10-Genel Muhasebe": "Bilanço Eşitliği, Tek Düzen Hesap Planı, Dönen/Duran Varlıklar, Yevmiye Defteri, Büyük Defter, Mizan, Gelir Tablosu.",
    "10-Temel Hukuk": "Hukukun Kaynakları, Hak Ehliyeti, Borçlar Hukuku, Sözleşmeler, Tacir ve Esnaf, Kıymetli Evrak, Sigorta Hukuku.",
    "10-Ekonomi": "Arz-Talep, Piyasa Dengesi, Enflasyon, Milli Gelir, Para ve Bankacılık, Merkez Bankası, Dış Ticaret.",
    "10-Klavye Teknikleri": "F Klavye Tuşları, Oturuş Düzeni, Süreli Yazım, Hatasız Yazım Kuralları, Rakam Tuşları.",
    
    "11-Bilgisayarlı Muhasebe": "ETA/Luca Şirket Açma, Stok/Cari Kart, Fatura İşleme, Muhasebe Fişleri (Tahsil/Tediye), Çek/Senet, KDV Beyannamesi.",
    "11-Maliyet Muhasebesi": "7A ve 7B Hesapları, Direkt İlk Madde (150), Direkt İşçilik (720), Genel Üretim (730), Satılan Mamul Maliyeti.",
    "11-Şirketler Muhasebesi": "Şirket Kuruluşu (Kolektif, A.Ş., Ltd.), Sermaye Artırımı, Kar Dağıtımı, Tasfiye, Birleşme.",
    "11-Vergi ve Beyannameler": "Vergi Usul Kanunu, Gelir Vergisi, Kurumlar Vergisi, KDV, ÖTV, MTV, Muhtasar Beyanname.",
    "11-İş ve Sosyal Güvenlik Hukuku": "İş Kanunu, İş Sözleşmesi, Kıdem Tazminatı, İhbar Tazminatı, Ücret Bordrosu, SGK 4a/4b/4c.",
    "11-Girişimcilik ve İşletme": "Girişimcilik Türleri, İş Planı, Fizibilite, Pazar Araştırması, KOSGEB Destekleri.",
    
    "12-Dış Ticaret": "İhracat/İthalat Rejimi, Teslim Şekilleri (Incoterms), Ödeme Şekilleri, Gümrük Mevzuatı, Kambiyo.",
    "12-Kooperatifçilik": "Kooperatif İlkeleri, Kuruluş, Ana Sözleşme, Ortaklık Hakları, Genel Kurul, Risturn.",
    "12-Hızlı Klavye": "İleri Seviye Yazım, Adli/Hukuki Metinler, Zabıt Kâtipliği Metinleri.",
    "12-Ahilik Kültürü ve Girişimcilik": "Ahilik Teşkilatı, Fütüvvetname, Usta-Çırak İlişkisi, Meslek Ahlakı, E-Ticaret."
}

# --- 3. GARANTİ YEDEK DEPO (Her ders için en az 5 soru - ASLA BOŞ DÖNMEZ) ---
YEDEK_DEPO = {
    "9-Temel Muhasebe": [
        {"soru": "Fatura yerine geçen belgelerden hangisi çiftçiden ürün alırken kullanılır?", "secenekler": ["Müstahsil Makbuzu", "Gider Pusulası", "Fatura", "Fiş", "İrsaliye"], "cevap": "Müstahsil Makbuzu"},
        {"soru": "İşletme defterinin gider sayfasına hangisi yazılır?", "secenekler": ["Mal alış bedeli", "Mal satış bedeli", "Kira geliri", "Faiz geliri", "Hizmet geliri"], "cevap": "Mal alış bedeli"},
        {"soru": "Malın sevki sırasında düzenlenen belge hangisidir?", "secenekler": ["Sevk İrsaliyesi", "Fatura", "Gider Pusulası", "Tahsilat Makbuzu", "Çek"], "cevap": "Sevk İrsaliyesi"},
        {"soru": "Serbest meslek erbabının (Doktor, Avukat) düzenlediği belge nedir?", "secenekler": ["Serbest Meslek Makbuzu", "Fatura", "Fiş", "Gider Pusulası", "İrsaliye"], "cevap": "Serbest Meslek Makbuzu"},
        {"soru": "Defterlerin saklama süresi kaç yıldır?", "secenekler": ["5 Yıl", "10 Yıl", "1 Yıl", "3 Yıl", "20 Yıl"], "cevap": "5 Yıl"}
    ],
    "10-Genel Muhasebe": [
        {"soru": "Bilanço temel denkliği hangisidir?", "secenekler": ["Varlıklar = Kaynaklar", "Gelir = Gider", "Aktif = Pasif - Sermaye", "Kasa = Banka", "Borç = Alacak"], "cevap": "Varlıklar = Kaynaklar"},
        {"soru": "100 Kasa hesabı nasıl çalışır?", "secenekler": ["Girişler Borç, Çıkışlar Alacak", "Girişler Alacak, Çıkışlar Borç", "Hep Alacaklı", "Hep Borçlu", "Çalışmaz"], "cevap": "Girişler Borç, Çıkışlar Alacak"},
        {"soru": "Satıcıya borçlandığımızda hangi hesap kullanılır?", "secenekler": ["320 Satıcılar", "120 Alıcılar", "102 Bankalar", "600 Satışlar", "500 Sermaye"], "cevap": "320 Satıcılar"},
        {"soru": "Dönem net karı hangi hesapta izlenir?", "secenekler": ["590 Dönem Net Karı", "600 Satışlar", "500 Sermaye", "100 Kasa", "320 Satıcılar"], "cevap": "590 Dönem Net Karı"},
        {"soru": "Mizan nedir?", "secenekler": ["Hesapların borç/alacak toplamlarını gösteren çizelge", "Mali durum tablosu", "Kar zarar tablosu", "Fatura listesi", "Vergi beyannamesi"], "cevap": "Hesapların borç/alacak toplamlarını gösteren çizelge"}
    ],
    "10-Temel Hukuk": [
        {"soru": "Hak ehliyeti ne zaman başlar?", "secenekler": ["Tam ve sağ doğumla", "18 yaşla", "Evlenince", "Okula başlayınca", "İşe girince"], "cevap": "Tam ve sağ doğumla"},
        {"soru": "Borcun unsurları nelerdir?", "secenekler": ["Alacaklı, Borçlu, Edim", "Hakim, Savcı, Avukat", "Para, Mal, Hizmet", "Yasa, Tüzük, Yönetmelik", "Davacı, Davalı, Tanık"], "cevap": "Alacaklı, Borçlu, Edim"},
        {"soru": "Tacir kime denir?", "secenekler": ["Ticari işletmeyi işleten kişi", "Devlet memuru", "Tüketici", "Öğrenci", "Dernek başkanı"], "cevap": "Ticari işletmeyi işleten kişi"},
        {"soru": "Hukukun yazılı kaynaklarından en üstünü hangisidir?", "secenekler": ["Anayasa", "Kanun", "Yönetmelik", "Genelge", "Örf Adet"], "cevap": "Anayasa"},
        {"soru": "Fiil ehliyetine sahip olmak için gereken yaş sınırı kaçtır?", "secenekler": ["18", "15", "21", "12", "25"], "cevap": "18"}
    ],
    "11-Maliyet Muhasebesi": [
        {"soru": "7/A seçeneğinde Direkt İlk Madde ve Malzeme Giderleri kodu nedir?", "secenekler": ["710", "720", "730", "740", "750"], "cevap": "710"},
        {"soru": "Direkt İşçilik Giderleri hangi hesapta izlenir?", "secenekler": ["720", "710", "730", "760", "770"], "cevap": "720"},
        {"soru": "150 İlk Madde ve Malzeme hesabı hangi gruptadır?", "secenekler": ["Stoklar", "Hazır Değerler", "Duran Varlıklar", "Maliyet Hesapları", "Gelir Hesapları"], "cevap": "Stoklar"},
        {"soru": "Satılan Mamul Maliyeti Tablosu neyi gösterir?", "secenekler": ["Üretilen ve satılan ürünün maliyetini", "Satış karını", "Kasa mevcudunu", "Banka borcunu", "Vergi borcunu"], "cevap": "Üretilen ve satılan ürünün maliyetini"},
        {"soru": "Hangisi bir maliyet gideri çeşididir?", "secenekler": ["Amortisman", "Kasa", "Çek", "Senet", "Banka"], "cevap": "Amortisman"}
    ],
    "11-Vergi ve Beyannameler": [
        {"soru": "KDV beyannamesi ne zaman verilir?", "secenekler": ["Takip eden ayın 28'i", "Yıl sonunda", "Her hafta", "Günlük", "3 ayda bir"], "cevap": "Takip eden ayın 28'i"},
        {"soru": "MTV (Motorlu Taşıtlar Vergisi) yılda kaç taksittir?", "secenekler": ["2 Taksit", "Tek seferde", "12 Taksit", "4 Taksit", "Ödenmez"], "cevap": "2 Taksit"},
        {"soru": "Gelir vergisinin konusu nedir?", "secenekler": ["Gerçek kişilerin gelirleri", "Şirket kazançları", "Harcamalar", "Emlak", "Veraset"], "cevap": "Gerçek kişilerin gelirleri"},
        {"soru": "Kurumlar Vergisi oranı (2024) yaklaşık kaçtır?", "secenekler": ["%25", "%10", "%50", "%1", "%5"], "cevap": "%25"},
        {"soru": "Muhtasar Beyanname ile ne beyan edilir?", "secenekler": ["Kesilen vergiler (Stopaj)", "KDV", "Yıllık gelir", "Emlak vergisi", "MTV"], "cevap": "Kesilen vergiler (Stopaj)"}
    ],
    "12-Dış Ticaret": [
        {"soru": "İhracat nedir?", "secenekler": ["Yurt dışına mal satmak", "Yurt dışından mal almak", "Üretim yapmak", "Vergi ödemek", "Depolama"], "cevap": "Yurt dışına mal satmak"},
        {"soru": "FOB teslim şekli ne anlama gelir?", "secenekler": ["Gemi güvertesinde teslim", "Fabrikada teslim", "Gümrükte teslim", "Sigorta dahil teslim", "Kapıda ödeme"], "cevap": "Gemi güvertesinde teslim"},
        {"soru": "Gümrük vergisi kime ödenir?", "secenekler": ["Gümrük İdaresine", "Belediyeye", "Satıcıya", "Alıcıya", "Nakliyeciye"], "cevap": "Gümrük İdaresine"},
        {"soru": "Akreditif nedir?", "secenekler": ["Banka garantili ödeme yöntemi", "Nakit ödeme", "Çek", "Senet", "Veresiye"], "cevap": "Banka garantili ödeme yöntemi"},
        {"soru": "İthalat nedir?", "secenekler": ["Yurt dışından mal almak", "Yurt dışına mal satmak", "Mal üretmek", "Hizmet vermek", "Yatırım yapmak"], "cevap": "Yurt dışından mal almak"}
    ],
    # GENEL YEDEK (Her ihtimale karşı)
    "Genel": [
        {"soru": "VUK'a göre fatura düzenleme sınırı (2025) aşıldığında hangi belge düzenlenmelidir?", "secenekler": ["Fatura", "Fiş", "Gider Pusulası", "İrsaliye", "Dekont"], "cevap": "Fatura"},
        {"soru": "Bilanço temel denkliği hangisidir?", "secenekler": ["Varlıklar = Kaynaklar", "Gelir = Gider", "Borç = Alacak", "Aktif = Pasif + Sermaye", "Kasa = Banka"], "cevap": "Varlıklar = Kaynaklar"},
        {"soru": "Excel'de 'EĞER' formülü ne işe yarar?", "secenekler": ["Mantıksal kıyaslama yapar", "Toplama yapar", "Ortalama alır", "Yazı rengini değiştirir", "Tablo çizer"], "cevap": "Mantıksal kıyaslama yapar"},
        {"soru": "KDV hariç 100 TL olan bir ürünün %20 KDV dahil fiyatı nedir?", "secenekler": ["120 TL", "100 TL", "118 TL", "110 TL", "102 TL"], "cevap": "120 TL"},
        {"soru": "Tacir kime denir?", "secenekler": ["Ticari işletmeyi işleten", "Memur", "İşçi", "Öğrenci", "Emekli"], "cevap": "Ticari işletmeyi işleten"}
    ]
}

# --- AI AYARLARI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def yapay_zeka_soru_uret(sinif, ders):
    ai_sorulari = []
    
    # Sınıf numarasını al (örn: "9. Sınıf" -> "9")
    sinif_no = sinif.split(".")[0]
    ders_key = f"{sinif_no}-{ders}" # Örn: "11-Vergi ve Beyannameler"
    
    # Konu Havuzundan Ders İçeriğini Al
    konu_metni = KONU_HAVUZU.get(ders_key, "Müfredat Konuları")
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Rolün: Lise Öğretmeni. Ders: {ders} ({sinif}).
        Müfredat Konuları: {konu_metni}
        
        GÖREV: Yukarıdaki konulardan TAM 10 ADET test sorusu üret.
        
        KURALLAR:
        1. SADECE belirtilen dersin konularından sor. (Örn: Hukuk dersinde muhasebe sorma).
        2. Her sorunun 5 şıkkı (A,B,C,D,E) olsun.
        3. Cevaplar rastgele şıklara dağılsın.
        4. Çıktı SADECE JSON olsun.
        
        JSON: [ {{ "soru": "...", "secenekler": ["A", "B", "C", "D", "E"], "cevap": "..." }} ]
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

    # GARANTİ MEKANİZMASI: 10 SORUYA TAMAMLA
    # Eğer AI eksik verdiyse veya çalışmadıysa yedekten çek
    if len(ai_sorulari) < 10:
        # 1. Tam eşleşen yedeği bul
        ozel_yedek = YEDEK_DEPO.get(ders_key, [])
        
        # 2. Bulamazsa Genel yedeği al
        if not ozel_yedek:
            ozel_yedek = YEDEK_DEPO["Genel"]
            
        eksik = 10 - len(ai_sorulari)
        
        # Yedeği karıştır ve ekle (Soru yetmezse kopyalayarak çoğalt)
        random.shuffle(ozel_yedek)
        while len(ozel_yedek) < eksik:
            ozel_yedek.extend(ozel_yedek)
            
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
        with st.status("Sorular Hazırlanıyor... Lütfen Bekleyiniz.", expanded=True):
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
    
    # Şıkları her seferinde karıştır
    secenekler = soru["secenekler"]
    random.shuffle(secenekler)
    
    for sec in secenekler:
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
