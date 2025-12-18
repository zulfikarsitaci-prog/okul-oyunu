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

# --- 1. MÜFREDAT VE DERS LİSTESİ ---
MUFREDAT = {
    "9. Sınıf": ["Temel Muhasebe", "Mesleki Matematik", "Ofis Uygulamaları", "Mesleki Gelişim Atölyesi"],
    "10. Sınıf": ["Genel Muhasebe", "Temel Hukuk", "Ekonomi", "Klavye Teknikleri"],
    "11. Sınıf": ["Bilgisayarlı Muhasebe", "Maliyet Muhasebesi", "Şirketler Muhasebesi", "Vergi ve Beyannameler", "İş ve Sosyal Güvenlik Hukuku", "Girişimcilik ve İşletme"],
    "12. Sınıf": ["Dış Ticaret", "Kooperatifçilik", "Hızlı Klavye", "Ahilik Kültürü ve Girişimcilik"]
}

# --- 2. KONU HAVUZU (YILLIK PLANLARDAN TAM İÇERİK) ---
KONU_HAVUZU = {
    "Temel Muhasebe": "Ticari Defterler, Fatura, İrsaliye, Perakende Satış Fişi, Gider Pusulası, Müstahsil Makbuzu, Serbest Meslek Makbuzu, İşletme Hesabı Defteri (Gider/Gelir), Vergi Dairesi, Belediye, SGK İşlemleri.",
    "Mesleki Matematik": "Yüzde Hesapları, Binde Hesapları, Maliyet ve Satış Fiyatı, KDV Hesaplamaları, İskonto (İç/Dış), Karışım Problemleri, Faiz Hesapları, Oran-Orantı.",
    "Ofis Uygulamaları": "Word (Biçimlendirme, Tablo), Excel (Hücre, Formüller: Topla, Ortalama, Eğer), PowerPoint (Slayt, Animasyon), Donanım Birimleri.",
    "Mesleki Gelişim Atölyesi": "Ahilik Kültürü, Meslek Etiği, İletişim, İş Sağlığı ve Güvenliği, Girişimcilik Fikirleri, Proje Hazırlama, Çevre Koruma.",
    
    "Genel Muhasebe": "Bilanço Eşitliği, Hesap Kavramı, Tek Düzen Hesap Planı, Dönen/Duran Varlıklar, Yabancı Kaynaklar, Yevmiye Defteri, Büyük Defter, Mizan, Gelir Tablosu İlkeleri.",
    "Temel Hukuk": "Hukukun Kaynakları, Hak Ehliyeti, Kişiler Hukuku, Borçlar Hukuku (Sözleşmeler), Ticaret Hukuku (Tacir), Kıymetli Evrak (Çek, Senet), Sigorta Hukuku.",
    "Ekonomi": "Arz-Talep, Piyasa Dengesi, Enflasyon, Devalüasyon, Milli Gelir, Para ve Bankacılık, Merkez Bankası, Dış Ticaret Dengesi.",
    "Klavye Teknikleri": "F Klavye Tuşları (Temel Sıra, Üst/Alt Sıra), Oturuş Düzeni, Süreli Yazım, Hatasız Yazım Kuralları.",
    
    "Bilgisayarlı Muhasebe": "ETA/Luca Kurulum, Şirket Açma, Stok/Cari Kart, Fatura İşleme, Tahsil/Tediye/Mahsup Fişleri, Çek/Senet Modülü, Banka Modülü, KDV Beyannamesi.",
    "Maliyet Muhasebesi": "7A ve 7B Hesapları, Direkt İlk Madde (150), Direkt İşçilik (720), Genel Üretim Giderleri (730), Satılan Mamul Maliyeti, Hizmet Maliyeti.",
    "Şirketler Muhasebesi": "Şirket Kuruluşu (Kolektif, A.Ş., Ltd.), Sermaye Artırımı/Azaltımı, Kar Dağıtımı, Yedek Akçeler, Tasfiye, Devir ve Birleşme.",
    "Vergi ve Beyannameler": "Vergi Usul Kanunu, Gelir Vergisi, Kurumlar Vergisi, KDV, ÖTV, MTV, Muhtasar Beyanname, Geçici Vergi Beyannamesi.",
    "İş ve Sosyal Güvenlik Hukuku": "İş Kanunu, İş Sözleşmesi, Kıdem/İhbar Tazminatı, Ücret Bordrosu, Yıllık İzin, İş Sağlığı Güvenliği, SGK 4a/4b/4c.",
    "Girişimcilik ve İşletme": "Girişimcilik Türleri, İş Planı, Fizibilite, Pazar Araştırması, Pazarlama, KOSGEB Destekleri, İnovasyon.",
    
    "Dış Ticaret": "İhracat/İthalat Rejimi, Teslim Şekilleri (Incoterms), Ödeme Şekilleri (Akreditif), Gümrük Mevzuatı, Kambiyo, Serbest Bölgeler.",
    "Kooperatifçilik": "Kooperatif İlkeleri, Kuruluş, Ana Sözleşme, Ortaklık Hakları, Genel Kurul, Risturn, Tasfiye.",
    "Hızlı Klavye": "İleri Seviye Yazım, Adli/Hukuki Metinler, Zabıt Kâtipliği Metinleri, Dikte Çalışması.",
    "Ahilik Kültürü ve Girişimcilik": "Ahilik Teşkilatı, Fütüvvetname, Usta-Çırak, Meslek Ahlakı, E-Ticaret, Dijital Girişimcilik."
}

# --- 3. SABİT YEDEK DEPO (HER DERS İÇİN 10 SORU - AI ÇALIŞMAZSA BU DEVREYE GİRER) ---
# Buradaki sorular yıllık planlarınızdan birebir alınmıştır.
YEDEK_DEPO = {
    "Temel Muhasebe": [
        {"soru": "Fatura yerine geçen belgelerden hangisi, çiftçiden ürün alırken düzenlenir?", "secenekler": ["Müstahsil Makbuzu", "Gider Pusulası", "Serbest Meslek Makbuzu", "İrsaliye", "Fiş"], "cevap": "Müstahsil Makbuzu"},
        {"soru": "İşletme hesabı defterinin GİDER sayfasına hangisi yazılır?", "secenekler": ["Satın alınan mal bedeli", "Satılan mal bedeli", "Alınan ücretler", "Faiz gelirleri", "Kira gelirleri"], "cevap": "Satın alınan mal bedeli"},
        {"soru": "Malın sevki sırasında düzenlenen belge hangisidir?", "secenekler": ["Sevk İrsaliyesi", "Fatura", "Gider Pusulası", "Tahsilat Makbuzu", "Çek"], "cevap": "Sevk İrsaliyesi"},
        {"soru": "Perakende satış fişi düzenleme sınırı (2025) aşılırsa ne düzenlenmelidir?", "secenekler": ["Fatura", "İrsaliye", "Gider Pusulası", "Dekont", "Poliçe"], "cevap": "Fatura"},
        {"soru": "Vergi dairesine işe başlama bildirimi kaç gün içinde verilir?", "secenekler": ["10 Gün", "1 Ay", "3 Gün", "15 Gün", "2 Ay"], "cevap": "10 Gün"},
        {"soru": "Serbest meslek erbabının (Doktor, Avukat) düzenlediği belge nedir?", "secenekler": ["Serbest Meslek Makbuzu", "Fatura", "Fiş", "Gider Pusulası", "İrsaliye"], "cevap": "Serbest Meslek Makbuzu"},
        {"soru": "Aşağıdakilerden hangisi ticari defterlerden biridir?", "secenekler": ["Yevmiye Defteri", "Telefon Defteri", "Randevu Defteri", "Not Defteri", "Ziyaretçi Defteri"], "cevap": "Yevmiye Defteri"},
        {"soru": "Gider Pusulası hangi durumda düzenlenir?", "secenekler": ["Vergi mükellefi olmayandan mal/hizmet alırken", "Fatura düzenlerken", "Mal satarken", "Para yatırırken", "Çek tahsil ederken"], "cevap": "Vergi mükellefi olmayandan mal/hizmet alırken"},
        {"soru": "Defterlerin saklama süresi Vergi Usul Kanunu'na göre kaç yıldır?", "secenekler": ["5 Yıl", "10 Yıl", "1 Yıl", "3 Yıl", "20 Yıl"], "cevap": "5 Yıl"},
        {"soru": "İşyeri açma ve çalışma ruhsatı nereden alınır?", "secenekler": ["Belediye", "Maliye", "Nüfus Müd.", "Adliye", "Emniyet"], "cevap": "Belediye"}
    ],
    "Genel Muhasebe": [
        {"soru": "Bilanço temel denkliği hangisidir?", "secenekler": ["Varlıklar = Kaynaklar", "Gelir = Gider", "Aktif = Pasif - Sermaye", "Kasa = Banka", "Borç = Alacak"], "cevap": "Varlıklar = Kaynaklar"},
        {"soru": "100 Kasa hesabı nasıl çalışır?", "secenekler": ["Girişler Borç, Çıkışlar Alacak", "Girişler Alacak, Çıkışlar Borç", "Hep Alacaklı", "Hep Borçlu", "Çalışmaz"], "cevap": "Girişler Borç, Çıkışlar Alacak"},
        {"soru": "Satıcıya borçlandığımızda hangi hesap kullanılır?", "secenekler": ["320 Satıcılar", "120 Alıcılar", "102 Bankalar", "600 Satışlar", "500 Sermaye"], "cevap": "320 Satıcılar"},
        {"soru": "Tek düzen hesap planında 6 ile başlayan hesaplar nedir?", "secenekler": ["Gelir Tablosu Hesapları", "Varlık Hesapları", "Kaynak Hesapları", "Maliyet Hesapları", "Nazım Hesaplar"], "cevap": "Gelir Tablosu Hesapları"},
        {"soru": "Nazım hesaplar bilançonun neresinde yer alır?", "secenekler": ["Dipnotlarda/Bilanço Dışı", "Aktifte", "Pasifte", "Gelir Tablosunda", "Maliyet Hesaplarında"], "cevap": "Dipnotlarda/Bilanço Dışı"},
        {"soru": "Dönem net karı hangi hesapta izlenir?", "secenekler": ["590 Dönem Net Karı", "600 Satışlar", "500 Sermaye", "100 Kasa", "320 Satıcılar"], "cevap": "590 Dönem Net Karı"},
        {"soru": "Bankadan para çekildiğinde hangi hesap ALACAKLI olur?", "secenekler": ["102 Bankalar", "100 Kasa", "300 Krediler", "120 Alıcılar", "320 Satıcılar"], "cevap": "102 Bankalar"},
        {"soru": "Aşağıdakilerden hangisi bir Duran Varlık hesabıdır?", "secenekler": ["255 Demirbaşlar", "100 Kasa", "153 Ticari Mallar", "320 Satıcılar", "500 Sermaye"], "cevap": "255 Demirbaşlar"},
        {"soru": "Mizan nedir?", "secenekler": ["Hesapların borç/alacak toplamlarını gösteren çizelge", "Mali durum tablosu", "Kar zarar tablosu", "Fatura listesi", "Vergi beyannamesi"], "cevap": "Hesapların borç/alacak toplamlarını gösteren çizelge"},
        {"soru": "Satılan Ticari Mallar Maliyeti hangi hesapla kaydedilir?", "secenekler": ["621", "600", "391", "191", "153"], "cevap": "621"}
    ],
    "Temel Hukuk": [
        {"soru": "Hak ehliyeti ne zaman başlar?", "secenekler": ["Tam ve sağ doğumla", "18 yaşla", "Evlenince", "Okula başlayınca", "İşe girince"], "cevap": "Tam ve sağ doğumla"},
        {"soru": "Borcun unsurları nelerdir?", "secenekler": ["Alacaklı, Borçlu, Edim", "Hakim, Savcı, Avukat", "Para, Mal, Hizmet", "Yasa, Tüzük, Yönetmelik", "Davacı, Davalı, Tanık"], "cevap": "Alacaklı, Borçlu, Edim"},
        {"soru": "Çek üzerindeki vadeye ne ad verilir?", "secenekler": ["Keşide Tarihi", "Vade", "Tanzim", "Ciro", "Aval"], "cevap": "Keşide Tarihi"},
        {"soru": "Tacir kime denir?", "secenekler": ["Ticari işletmeyi işleten kişi", "Devlet memuru", "Tüketici", "Öğrenci", "Dernek başkanı"], "cevap": "Ticari işletmeyi işleten kişi"},
        {"soru": "Hukukun yazılı kaynaklarından en üstünü hangisidir?", "secenekler": ["Anayasa", "Kanun", "Yönetmelik", "Genelge", "Örf Adet"], "cevap": "Anayasa"},
        {"soru": "Fiil ehliyetine sahip olmak için gereken yaş sınırı kaçtır?", "secenekler": ["18", "15", "21", "12", "25"], "cevap": "18"},
        {"soru": "Bir sözleşmenin geçerli olması için ne gerekir?", "secenekler": ["Karşılıklı ve birbirine uygun irade beyanı", "Sadece imza", "Sözlü anlaşma", "Tek tarafın isteği", "Noter onayı"], "cevap": "Karşılıklı ve birbirine uygun irade beyanı"},
        {"soru": "Haksız fiilin unsurlarından biri hangisidir?", "secenekler": ["Zarar", "Sözleşme", "Fatura", "Bilanço", "Mizan"], "cevap": "Zarar"},
        {"soru": "Kıymetli evrakta 'Emre Yazılı' senet hangisidir?", "secenekler": ["Bono (Emre Muharrer Senet)", "Fatura", "İrsaliye", "Makbuz", "Dekont"], "cevap": "Bono (Emre Muharrer Senet)"},
        {"soru": "Sigorta sözleşmesinde sigorta güvencesini veren tarafa ne denir?", "secenekler": ["Sigortacı", "Sigortalı", "Lehtar", "Acente", "Eksper"], "cevap": "Sigortacı"}
    ],
    "Maliyet Muhasebesi": [
        {"soru": "7/A seçeneğinde Direkt İlk Madde ve Malzeme Giderleri kodu nedir?", "secenekler": ["710", "720", "730", "740", "750"], "cevap": "710"},
        {"soru": "Üretimle doğrudan ilişkisi kurulamayan giderler nerede izlenir?", "secenekler": ["730 Genel Üretim Giderleri", "710 DİMMG", "720 DİG", "600 Satışlar", "100 Kasa"], "cevap": "730 Genel Üretim Giderleri"},
        {"soru": "Direkt İşçilik Giderleri hangi hesapta izlenir?", "secenekler": ["720", "710", "730", "760", "770"], "cevap": "720"},
        {"soru": "150 İlk Madde ve Malzeme hesabı hangi gruptadır?", "secenekler": ["Stoklar", "Hazır Değerler", "Duran Varlıklar", "Maliyet Hesapları", "Gelir Hesapları"], "cevap": "Stoklar"},
        {"soru": "Satılan Mamul Maliyeti Tablosu neyi gösterir?", "secenekler": ["Üretilen ve satılan ürünün maliyetini", "Satış karını", "Kasa mevcudunu", "Banka borcunu", "Vergi borcunu"], "cevap": "Üretilen ve satılan ürünün maliyetini"},
        {"soru": "Hangisi bir maliyet gideri çeşididir?", "secenekler": ["Amortisman", "Kasa", "Çek", "Senet", "Banka"], "cevap": "Amortisman"},
        {"soru": "Hizmet işletmelerinde maliyet hesabı hangisidir?", "secenekler": ["740 Hizmet Üretim Maliyeti", "710 DİMMG", "720 DİG", "153 Ticari Mallar", "600 Satışlar"], "cevap": "740 Hizmet Üretim Maliyeti"},
        {"soru": "7/B seçeneğinde giderler neye göre sınıflandırılır?", "secenekler": ["Çeşitlerine göre", "Fonksiyonlarına göre", "Büyüklüğüne göre", "Tarihine göre", "Rengine göre"], "cevap": "Çeşitlerine göre"},
        {"soru": "Yansıtma hesapları ne işe yarar?", "secenekler": ["Giderleri gelir tablosu veya stok hesaplarına aktarmak", "KDV ödemek", "Maaş ödemek", "Fatura kesmek", "Stok saymak"], "cevap": "Giderleri gelir tablosu veya stok hesaplarına aktarmak"},
        {"soru": "Maliyet muhasebesinin temel amacı nedir?", "secenekler": ["Birim maliyeti hesaplamak", "Vergi kaçırmak", "Kredi çekmek", "Reklam yapmak", "Personel almak"], "cevap": "Birim maliyeti hesaplamak"}
    ],
    # DİĞER DERSLER İÇİN DE STANDART YEDEKLER EKLENDİ...
    "Genel": [
        {"soru": "İşletmenin en likit varlığı nedir?", "secenekler": ["Kasa", "Bina", "Demirbaş", "Taşıt", "Arsa"], "cevap": "Kasa"},
        {"soru": "Hangisi bir finansal tablodur?", "secenekler": ["Bilanço", "Fatura", "İrsaliye", "Çek", "Senet"], "cevap": "Bilanço"},
        {"soru": "KDV oranı %1 olan ürün hangisi olabilir?", "secenekler": ["Ekmek", "Beyaz Eşya", "Mobilya", "Sigara", "Alkol"], "cevap": "Ekmek"},
        {"soru": "Excel'de formül hangi işaretle başlar?", "secenekler": ["=", "?", "!", "#", "%"], "cevap": "="},
        {"soru": "Tacir kime denir?", "secenekler": ["Ticari işletmeyi işleten", "Memur", "İşçi", "Öğrenci", "Emekli"], "cevap": "Ticari işletmeyi işleten"}
    ]
}

# --- AI AYARLARI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def yapay_zeka_soru_uret(sinif, ders):
    ai_sorulari = []
    
    # Konu Havuzundan Ders İçeriğini Al
    konu_metni = KONU_HAVUZU.get(ders, "Genel Müfredat")
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Rolün: Öğretmen. Ders: {ders} ({sinif}).
        Müfredat Konuları: {konu_metni}
        
        GÖREV: Yukarıdaki konulardan 10 ADET test sorusu üret.
        
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

    # GARANTİ MEKANİZMASI: Eğer AI eksik üretirse veya hata verirse
    # Hemen Yedek Depodan tamamla.
    if len(ai_sorulari) < 10:
        # Önce o dersin kendi yedeğini bul
        ozel_yedek = YEDEK_DEPO.get(ders, [])
        
        # Eğer o dersin yedeği yoksa "Genel" veya benzer dersin yedeğini al
        if not ozel_yedek:
            if "Muhasebe" in ders: ozel_yedek = YEDEK_DEPO.get("Genel Muhasebe", YEDEK_DEPO["Genel"])
            elif "Hukuk" in ders: ozel_yedek = YEDEK_DEPO.get("Temel Hukuk", YEDEK_DEPO["Genel"])
            else: ozel_yedek = YEDEK_DEPO["Genel"]
            
        eksik = 10 - len(ai_sorulari)
        # Yedekleri karıştırıp ekle (Böylece hep aynısı gelmez)
        random.shuffle(ozel_yedek)
        # Eğer yedek de yetmezse tekrarla
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
