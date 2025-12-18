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

# --- GÖRÜNTÜ AYARLARI (IHLAMUR YEŞİLİ & SARI KİREMİT) ---
st.markdown("""
    <style>
    /* 1. Arka Plan: Ihlamur Yeşili (Ferah ve Okunaklı) */
    .stApp {
        background-color: #F0F4C3 !important; 
    }
    
    /* 2. Tüm Yazılar: Simsiyah ve Net */
    h1, h2, h3, h4, h5, h6, p, div, span, label, li, .stMarkdown {
        color: #000000 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* 3. Butonlar: Sarı Kiremit (Dikkat Çekici) */
    .stButton>button { 
        width: 100%; 
        border-radius: 12px; 
        min-height: 4.5em; 
        font-weight: 700; 
        background-color: #FFB74D !important; /* Sarı Kiremit / Turuncumsu */
        color: #000000 !important; 
        border: 2px solid #E65100 !important; /* Koyu Kiremit Çerçeve */
        white-space: pre-wrap; 
        text-align: left !important; 
        padding: 15px;
        transition: all 0.3s ease;
        box-shadow: 3px 3px 0px rgba(0,0,0,0.2);
    }
    
    /* Üzerine gelince */
    .stButton>button:hover { 
        background-color: #FFA726 !important; 
        border-color: #000000 !important; 
        transform: translateY(-2px);
    }
    
    /* 4. Giriş Kutuları */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important; 
        color: #000000 !important; 
        border: 2px solid #E65100 !important;
    }
    
    /* 5. Soru Alanı */
    .big-font { 
        font-size: 22px !important; 
        font-weight: 800; 
        color: #000000 !important; 
        margin-bottom: 25px; 
        padding: 20px; 
        background-color: rgba(255,255,255,0.6); 
        border-left: 8px solid #E65100;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 1. DERS MÜFREDATI (Yıllık Planlara Göre Tam Liste) ---
MUFREDAT = {
    "9. Sınıf": ["Temel Muhasebe", "Mesleki Matematik", "Ofis Uygulamaları", "Mesleki Gelişim Atölyesi"],
    "10. Sınıf": ["Genel Muhasebe", "Temel Hukuk", "Ekonomi", "Klavye Teknikleri"],
    "11. Sınıf": ["Bilgisayarlı Muhasebe", "Maliyet Muhasebesi", "Şirketler Muhasebesi", "Vergi ve Beyannameler", "İş ve Sosyal Güvenlik Hukuku", "Girişimcilik"],
    "12. Sınıf": ["Dış Ticaret", "Kooperatifçilik", "Hızlı Klavye", "Ahilik Kültürü"]
}

# --- 2. DETAYLI KONU HAVUZU (18 DERS İÇİN AYRI AYRI) ---
# Yapay Zeka SADECE bu konuları kullanacak. Karışıklık İmkansız.
KONU_HAVUZU = {
    # 9. SINIF
    "9-Temel Muhasebe": "Ticari Defterler, Fatura, İrsaliye, Perakende Satış Fişi, Gider Pusulası, Müstahsil Makbuzu, Serbest Meslek Makbuzu, İşletme Hesabı Defteri (Gider/Gelir), Vergi Dairesi, Belediye, SGK İşlemleri.",
    "9-Mesleki Matematik": "Yüzde Hesapları, Binde Hesapları, Maliyet ve Satış Fiyatı, KDV Hesaplamaları, İskonto (İç/Dış), Karışım Problemleri, Faiz Hesapları, Oran-Orantı.",
    "9-Ofis Uygulamaları": "Word (Biçimlendirme, Tablo), Excel (Hücre, Formüller: Topla, Ortalama, Eğer), PowerPoint (Slayt, Animasyon), Donanım Birimleri.",
    "9-Mesleki Gelişim Atölyesi": "Ahilik Kültürü, Meslek Etiği, İletişim Türleri, İş Sağlığı ve Güvenliği, Girişimcilik Fikirleri, Proje Hazırlama, Çevre Koruma.",
    
    # 10. SINIF
    "10-Genel Muhasebe": "Bilanço Eşitliği, Hesap Kavramı, Tek Düzen Hesap Planı, Dönen/Duran Varlıklar, Yabancı Kaynaklar, Yevmiye Defteri, Büyük Defter, Mizan, Gelir Tablosu İlkeleri.",
    "10-Temel Hukuk": "Hukukun Kaynakları, Hak Ehliyeti, Kişiler Hukuku, Borçlar Hukuku (Sözleşmeler), Ticaret Hukuku (Tacir), Kıymetli Evrak (Çek, Senet), Sigorta Hukuku.",
    "10-Ekonomi": "Arz-Talep, Piyasa Dengesi, Enflasyon, Devalüasyon, Milli Gelir, Para ve Bankacılık, Merkez Bankası, Dış Ticaret Dengesi.",
    "10-Klavye Teknikleri": "F Klavye Tuşları (Temel Sıra, Üst/Alt Sıra), Oturuş Düzeni, Süreli Yazım, Hatasız Yazım Kuralları, Rakam Tuşları.",
    
    # 11. SINIF
    "11-Bilgisayarlı Muhasebe": "ETA/Luca Şirket Açma, Stok/Cari Kart, Fatura İşleme, Muhasebe Fişleri (Tahsil/Tediye), Çek/Senet, KDV Beyannamesi.",
    "11-Maliyet Muhasebesi": "7A ve 7B Hesapları, Direkt İlk Madde (150), Direkt İşçilik (720), Genel Üretim (730), Satılan Mamul Maliyeti, Hizmet Maliyeti.",
    "11-Şirketler Muhasebesi": "Şirket Kuruluşu (Kolektif, A.Ş., Ltd.), Sermaye Artırımı, Kar Dağıtımı, Tasfiye, Birleşme.",
    "11-Vergi ve Beyannameler": "Vergi Usul Kanunu, Gelir Vergisi, Kurumlar Vergisi, KDV, ÖTV, MTV, Muhtasar Beyanname, Geçici Vergi Beyannamesi.",
    "11-İş ve Sosyal Güvenlik Hukuku": "İş Kanunu, İş Sözleşmesi, Kıdem Tazminatı, İhbar Tazminatı, Ücret Bordrosu, SGK 4a/4b/4c.",
    "11-Girişimcilik": "Girişimcilik Türleri, İş Planı, Fizibilite, Pazar Araştırması, KOSGEB Destekleri, İnovasyon.",
    
    # 12. SINIF
    "12-Dış Ticaret": "İhracat/İthalat Rejimi, Teslim Şekilleri (Incoterms), Ödeme Şekilleri, Gümrük Mevzuatı, Kambiyo, Serbest Bölgeler.",
    "12-Kooperatifçilik": "Kooperatif İlkeleri, Kuruluş, Ana Sözleşme, Ortaklık Hakları, Genel Kurul, Risturn.",
    "12-Hızlı Klavye": "İleri Seviye Yazım, Adli/Hukuki Metinler, Zabıt Kâtipliği Metinleri.",
    "12-Ahilik Kültürü": "Ahilik Teşkilatı, Fütüvvetname, Usta-Çırak İlişkisi, Meslek Ahlakı, E-Ticaret."
}

# --- 3. GARANTİ YEDEK DEPO (HER DERS İÇİN 10 SORU) ---
# AI çalışmazsa sistem buraya bakar. ASLA BAŞKA DERSİN SORUSU ÇIKMAZ.
YEDEK_DEPO = {
    # --- 9. SINIF ---
    "9-Temel Muhasebe": [
        {"soru": "Fatura yerine geçen belgelerden hangisi çiftçiden ürün alırken kullanılır?", "secenekler": ["Müstahsil Makbuzu", "Gider Pusulası", "Fatura", "Fiş", "İrsaliye"], "cevap": "Müstahsil Makbuzu"},
        {"soru": "İşletme defterinin gider sayfasına hangisi yazılır?", "secenekler": ["Mal alış bedeli", "Mal satış bedeli", "Kira geliri", "Faiz geliri", "Hizmet geliri"], "cevap": "Mal alış bedeli"},
        {"soru": "Malın sevki sırasında düzenlenen belge hangisidir?", "secenekler": ["Sevk İrsaliyesi", "Fatura", "Gider Pusulası", "Tahsilat Makbuzu", "Çek"], "cevap": "Sevk İrsaliyesi"},
        {"soru": "Perakende satış fişi düzenleme sınırı (2025) aşılırsa ne düzenlenmelidir?", "secenekler": ["Fatura", "İrsaliye", "Gider Pusulası", "Dekont", "Poliçe"], "cevap": "Fatura"},
        {"soru": "Vergi dairesine işe başlama bildirimi kaç gün içinde verilir?", "secenekler": ["10 Gün", "1 Ay", "3 Gün", "15 Gün", "2 Ay"], "cevap": "10 Gün"},
        {"soru": "Serbest meslek erbabının (Doktor, Avukat) düzenlediği belge nedir?", "secenekler": ["Serbest Meslek Makbuzu", "Fatura", "Fiş", "Gider Pusulası", "İrsaliye"], "cevap": "Serbest Meslek Makbuzu"},
        {"soru": "Ticari defterlerin saklama süresi kaç yıldır?", "secenekler": ["5 Yıl", "10 Yıl", "1 Yıl", "3 Yıl", "20 Yıl"], "cevap": "5 Yıl"},
        {"soru": "İşyeri açma ruhsatı nereden alınır?", "secenekler": ["Belediye", "Maliye", "Nüfus Müd.", "Adliye", "Emniyet"], "cevap": "Belediye"},
        {"soru": "Gider Pusulası kimler için düzenlenir?", "secenekler": ["Vergi mükellefi olmayanlar", "Şirketler", "Tacirler", "Esnaflar", "Bankalar"], "cevap": "Vergi mükellefi olmayanlar"},
        {"soru": "Defter beyan sistemine giriş şifresi nereden alınır?", "secenekler": ["Vergi Dairesi", "Belediye", "Noter", "SGK", "Banka"], "cevap": "Vergi Dairesi"}
    ],
    "9-Mesleki Matematik": [
        {"soru": "KDV hariç 500 TL olan malın %20 KDV tutarı kaçtır?", "secenekler": ["100 TL", "50 TL", "20 TL", "120 TL", "80 TL"], "cevap": "100 TL"},
        {"soru": "Maliyeti 200 TL olan bir ürün %50 karla kaça satılır?", "secenekler": ["300 TL", "250 TL", "400 TL", "350 TL", "220 TL"], "cevap": "300 TL"},
        {"soru": "Yarısının 3 fazlası 13 olan sayı kaçtır?", "secenekler": ["20", "10", "15", "25", "18"], "cevap": "20"},
        {"soru": "Bir işçi günde 8 saat çalışarak bir işi 5 günde bitirirse, 10 saat çalışarak kaç günde bitirir?", "secenekler": ["4 Gün", "3 Gün", "6 Gün", "2 Gün", "5 Gün"], "cevap": "4 Gün"},
        {"soru": "1000 TL'nin %10'u kaç TL eder?", "secenekler": ["100 TL", "10 TL", "110 TL", "50 TL", "1000 TL"], "cevap": "100 TL"},
        {"soru": "Etiket fiyatı 400 TL olan bir ürüne %25 indirim yapılırsa yeni fiyat ne olur?", "secenekler": ["300 TL", "350 TL", "250 TL", "100 TL", "375 TL"], "cevap": "300 TL"},
        {"soru": "Bir kırtasiyeci 50 kuruşa aldığı kalemi 1 TL'ye satarsa kar oranı yüzde kaçtır?", "secenekler": ["%100", "%50", "%25", "%10", "%200"], "cevap": "%100"},
        {"soru": "Basit faiz formülünde (A.n.t/100) 'n' neyi ifade eder?", "secenekler": ["Faiz Oranını", "Anaparayı", "Zamanı", "Vergiyi", "Kar Payını"], "cevap": "Faiz Oranını"},
        {"soru": "Aşağıdaki oranlardan hangisi 'Yarım'ı ifade eder?", "secenekler": ["%50", "%25", "%10", "%100", "%75"], "cevap": "%50"},
        {"soru": "Bir malın alış fiyatı üzerine yapılan giderler eklenince ne bulunur?", "secenekler": ["Maliyet Fiyatı", "Satış Fiyatı", "Kar", "Ciro", "Zarar"], "cevap": "Maliyet Fiyatı"}
    ],
    "9-Ofis Uygulamaları": [
        {"soru": "Excel'de toplama formülü hangisidir?", "secenekler": ["=TOPLA()", "=ÇIKAR()", "=SAY()", "=EĞER()", "=ORTALAMA()"], "cevap": "=TOPLA()"},
        {"soru": "Word'de kaydetme kısayolu nedir?", "secenekler": ["CTRL+S", "CTRL+C", "CTRL+V", "CTRL+P", "CTRL+Z"], "cevap": "CTRL+S"},
        {"soru": "Sunum hazırlama programı hangisidir?", "secenekler": ["PowerPoint", "Excel", "Word", "Access", "Outlook"], "cevap": "PowerPoint"},
        {"soru": "Klavye üzerindeki en uzun tuş hangisidir?", "secenekler": ["Boşluk (Space)", "Enter", "Shift", "Ctrl", "Alt"], "cevap": "Boşluk (Space)"},
        {"soru": "Excel'de formüller hangi işaretle başlar?", "secenekler": ["=", "+", "-", "*", "/"], "cevap": "="},
        {"soru": "Bilgisayarın beyni olarak bilinen donanım hangisidir?", "secenekler": ["İşlemci (CPU)", "Ram", "Harddisk", "Anakart", "Ekran Kartı"], "cevap": "İşlemci (CPU)"},
        {"soru": "Metni kopyalamak için hangi kısayol kullanılır?", "secenekler": ["CTRL+C", "CTRL+V", "CTRL+X", "CTRL+P", "CTRL+A"], "cevap": "CTRL+C"},
        {"soru": "Aşağıdakilerden hangisi bir çıkış birimidir?", "secenekler": ["Yazıcı", "Klavye", "Mouse", "Tarayıcı", "Mikrofon"], "cevap": "Yazıcı"},
        {"soru": "Word'de metni kalın yapmak için hangi harf kullanılır?", "secenekler": ["K", "T", "A", "S", "Y"], "cevap": "K"},
        {"soru": "Excel'de A1 ile A5 arasındaki sayıların ortalamasını alan formül nedir?", "secenekler": ["=ORTALAMA(A1:A5)", "=TOPLA(A1:A5)", "=SAY(A1:A5)", "=MAK(A1:A5)", "=MİN(A1:A5)"], "cevap": "=ORTALAMA(A1:A5)"}
    ],
    
    # --- 10. SINIF ---
    "10-Genel Muhasebe": [
        {"soru": "Bilanço temel denkliği hangisidir?", "secenekler": ["Varlıklar = Kaynaklar", "Gelir = Gider", "Aktif = Pasif - Sermaye", "Kasa = Banka", "Borç = Alacak"], "cevap": "Varlıklar = Kaynaklar"},
        {"soru": "100 Kasa hesabı nasıl çalışır?", "secenekler": ["Girişler Borç, Çıkışlar Alacak", "Girişler Alacak, Çıkışlar Borç", "Hep Alacaklı", "Hep Borçlu", "Çalışmaz"], "cevap": "Girişler Borç, Çıkışlar Alacak"},
        {"soru": "Satıcıya borçlandığımızda hangi hesap kullanılır?", "secenekler": ["320 Satıcılar", "120 Alıcılar", "102 Bankalar", "600 Satışlar", "500 Sermaye"], "cevap": "320 Satıcılar"},
        {"soru": "Dönem net karı hangi hesapta izlenir?", "secenekler": ["590 Dönem Net Karı", "600 Satışlar", "500 Sermaye", "100 Kasa", "320 Satıcılar"], "cevap": "590 Dönem Net Karı"},
        {"soru": "Mizan nedir?", "secenekler": ["Hesapların borç/alacak toplamlarını gösteren çizelge", "Mali durum tablosu", "Kar zarar tablosu", "Fatura listesi", "Vergi beyannamesi"], "cevap": "Hesapların borç/alacak toplamlarını gösteren çizelge"},
        {"soru": "Bankadan para çekildiğinde hangi hesap ALACAKLI olur?", "secenekler": ["102 Bankalar", "100 Kasa", "300 Krediler", "120 Alıcılar", "320 Satıcılar"], "cevap": "102 Bankalar"},
        {"soru": "Aşağıdakilerden hangisi bir Duran Varlık hesabıdır?", "secenekler": ["255 Demirbaşlar", "100 Kasa", "153 Ticari Mallar", "320 Satıcılar", "500 Sermaye"], "cevap": "255 Demirbaşlar"},
        {"soru": "Tek düzen hesap planında 6 ile başlayan hesaplar nedir?", "secenekler": ["Gelir Tablosu Hesapları", "Varlık Hesapları", "Kaynak Hesapları", "Maliyet Hesapları", "Nazım Hesaplar"], "cevap": "Gelir Tablosu Hesapları"},
        {"soru": "Nazım hesaplar bilançonun neresinde yer alır?", "secenekler": ["Dipnotlarda/Bilanço Dışı", "Aktifte", "Pasifte", "Gelir Tablosunda", "Maliyet Hesaplarında"], "cevap": "Dipnotlarda/Bilanço Dışı"},
        {"soru": "Satılan Ticari Mallar Maliyeti hangi hesapla kaydedilir?", "secenekler": ["621", "600", "391", "191", "153"], "cevap": "621"}
    ],
    "10-Temel Hukuk": [
        {"soru": "Hak ehliyeti ne zaman başlar?", "secenekler": ["Tam ve sağ doğumla", "18 yaşla", "Evlenince", "Okula başlayınca", "İşe girince"], "cevap": "Tam ve sağ doğumla"},
        {"soru": "Borcun unsurları nelerdir?", "secenekler": ["Alacaklı, Borçlu, Edim", "Hakim, Savcı, Avukat", "Para, Mal, Hizmet", "Yasa, Tüzük, Yönetmelik", "Davacı, Davalı, Tanık"], "cevap": "Alacaklı, Borçlu, Edim"},
        {"soru": "Tacir kime denir?", "secenekler": ["Ticari işletmeyi işleten kişi", "Devlet memuru", "Tüketici", "Öğrenci", "Dernek başkanı"], "cevap": "Ticari işletmeyi işleten kişi"},
        {"soru": "Hukukun yazılı kaynaklarından en üstünü hangisidir?", "secenekler": ["Anayasa", "Kanun", "Yönetmelik", "Genelge", "Örf Adet"], "cevap": "Anayasa"},
        {"soru": "Fiil ehliyetine sahip olmak için gereken yaş sınırı kaçtır?", "secenekler": ["18", "15", "21", "12", "25"], "cevap": "18"},
        {"soru": "Bir sözleşmenin geçerli olması için ne gerekir?", "secenekler": ["Karşılıklı ve birbirine uygun irade beyanı", "Sadece imza", "Sözlü anlaşma", "Tek tarafın isteği", "Noter onayı"], "cevap": "Karşılıklı ve birbirine uygun irade beyanı"},
        {"soru": "Haksız fiilin unsurlarından biri hangisidir?", "secenekler": ["Zarar", "Sözleşme", "Fatura", "Bilanço", "Mizan"], "cevap": "Zarar"},
        {"soru": "Kıymetli evrakta 'Emre Yazılı' senet hangisidir?", "secenekler": ["Bono (Emre Muharrer Senet)", "Fatura", "İrsaliye", "Makbuz", "Dekont"], "cevap": "Bono (Emre Muharrer Senet)"},
        {"soru": "Sigorta sözleşmesinde sigorta güvencesini veren tarafa ne denir?", "secenekler": ["Sigortacı", "Sigortalı", "Lehtar", "Acente", "Eksper"], "cevap": "Sigortacı"},
        {"soru": "Çek üzerindeki vadeye ne ad verilir?", "secenekler": ["Keşide Tarihi", "Vade", "Tanzim", "Ciro", "Aval"], "cevap": "Keşide Tarihi"}
    ],
    "10-Ekonomi": [
        {"soru": "İnsan ihtiyaçlarını karşılayan mal ve hizmetlerin az olmasına ne denir?", "secenekler": ["Kıtlık", "Bolluk", "Enflasyon", "Fayda", "Tüketim"], "cevap": "Kıtlık"},
        {"soru": "Bir malın fiyatı artarsa talebi ne olur?", "secenekler": ["Azalır", "Artar", "Değişmez", "Sıfırlanır", "Çoğalır"], "cevap": "Azalır"},
        {"soru": "Fiyatlar genel düzeyinin sürekli artmasına ne denir?", "secenekler": ["Enflasyon", "Devalüasyon", "Resesyon", "Deflasyon", "Kriz"], "cevap": "Enflasyon"},
        {"soru": "Üretim faktörleri nelerdir?", "secenekler": ["Emek, Sermaye, Doğal Kaynak, Girişimci", "Para, Banka, Çek, Senet", "Alıcı, Satıcı, Devlet, Vergi", "Mal, Hizmet, Fayda, Zarar", "İnsan, Makine, Bina, Arsa"], "cevap": "Emek, Sermaye, Doğal Kaynak, Girişimci"},
        {"soru": "Hangisi bir 'Tam Rekabet Piyasası' özelliğidir?", "secenekler": ["Çok sayıda alıcı ve satıcı vardır", "Tek satıcı vardır", "Fiyatı devlet belirler", "Rekabet yasaktır", "Mal çeşitliliği azdır"], "cevap": "Çok sayıda alıcı ve satıcı vardır"},
        {"soru": "GSYİH (Gayri Safi Yurtiçi Hasıla) neyi ölçer?", "secenekler": ["Bir ülkedeki toplam üretimi", "Toplam borcu", "Döviz kurunu", "İşsizlik oranını", "Vergi gelirini"], "cevap": "Bir ülkedeki toplam üretimi"},
        {"soru": "Para politikasını hangi kurum yönetir?", "secenekler": ["Merkez Bankası", "Maliye Bakanlığı", "Belediyeler", "Özel Bankalar", "Borsa"], "cevap": "Merkez Bankası"},
        {"soru": "Bir ülkenin parasının yabancı paralar karşısında değer kaybetmesine ne denir?", "secenekler": ["Devalüasyon", "Revalüasyon", "Enflasyon", "Deflasyon", "Stagflasyon"], "cevap": "Devalüasyon"},
        {"soru": "Hangisi bir uluslararası ekonomik kuruluştur?", "secenekler": ["IMF", "FIFA", "UNESCO", "WHO", "NATO"], "cevap": "IMF"},
        {"soru": "İhracatın ithalattan fazla olması durumuna ne denir?", "secenekler": ["Dış Ticaret Fazlası", "Dış Ticaret Açığı", "Bütçe Açığı", "Enflasyon", "Devalüasyon"], "cevap": "Dış Ticaret Fazlası"}
    ],
    
    # --- 11. SINIF ---
    "11-Maliyet Muhasebesi": [
        {"soru": "7/A seçeneğinde Direkt İlk Madde ve Malzeme Giderleri kodu nedir?", "secenekler": ["710", "720", "730", "740", "750"], "cevap": "710"},
        {"soru": "Direkt İşçilik Giderleri hangi hesapta izlenir?", "secenekler": ["720", "710", "730", "760", "770"], "cevap": "720"},
        {"soru": "150 İlk Madde ve Malzeme hesabı hangi gruptadır?", "secenekler": ["Stoklar", "Hazır Değerler", "Duran Varlıklar", "Maliyet Hesapları", "Gelir Hesapları"], "cevap": "Stoklar"},
        {"soru": "Satılan Mamul Maliyeti Tablosu neyi gösterir?", "secenekler": ["Üretilen ve satılan ürünün maliyetini", "Satış karını", "Kasa mevcudunu", "Banka borcunu", "Vergi borcunu"], "cevap": "Üretilen ve satılan ürünün maliyetini"},
        {"soru": "Hangisi bir maliyet gideri çeşididir?", "secenekler": ["Amortisman", "Kasa", "Çek", "Senet", "Banka"], "cevap": "Amortisman"},
        {"soru": "Üretimle doğrudan ilişkisi kurulamayan giderler nerede izlenir?", "secenekler": ["730 Genel Üretim Giderleri", "710 DİMMG", "720 DİG", "600 Satışlar", "100 Kasa"], "cevap": "730 Genel Üretim Giderleri"},
        {"soru": "Hizmet işletmelerinde maliyet hesabı hangisidir?", "secenekler": ["740 Hizmet Üretim Maliyeti", "710 DİMMG", "720 DİG", "153 Ticari Mallar", "600 Satışlar"], "cevap": "740 Hizmet Üretim Maliyeti"},
        {"soru": "7/B seçeneğinde giderler neye göre sınıflandırılır?", "secenekler": ["Çeşitlerine göre", "Fonksiyonlarına göre", "Büyüklüğüne göre", "Tarihine göre", "Rengine göre"], "cevap": "Çeşitlerine göre"},
        {"soru": "Yansıtma hesapları ne işe yarar?", "secenekler": ["Giderleri gelir tablosu veya stok hesaplarına aktarmak", "KDV ödemek", "Maaş ödemek", "Fatura kesmek", "Stok saymak"], "cevap": "Giderleri gelir tablosu veya stok hesaplarına aktarmak"},
        {"soru": "Maliyet muhasebesinin temel amacı nedir?", "secenekler": ["Birim maliyeti hesaplamak", "Vergi kaçırmak", "Kredi çekmek", "Reklam yapmak", "Personel almak"], "cevap": "Birim maliyeti hesaplamak"}
    ],
    "11-Vergi ve Beyannameler": [
        {"soru": "KDV beyannamesi ne zaman verilir?", "secenekler": ["Takip eden ayın 28'i", "Yıl sonunda", "Her hafta", "Günlük", "3 ayda bir"], "cevap": "Takip eden ayın 28'i"},
        {"soru": "MTV (Motorlu Taşıtlar Vergisi) yılda kaç taksittir?", "secenekler": ["2 Taksit", "Tek seferde", "12 Taksit", "4 Taksit", "Ödenmez"], "cevap": "2 Taksit"},
        {"soru": "Gelir vergisinin konusu nedir?", "secenekler": ["Gerçek kişilerin kazançları", "Şirket kazançları", "Harcamalar", "Emlak", "Miras"], "cevap": "Gerçek kişilerin kazançları"},
        {"soru": "Hangisi dolaylı bir vergidir?", "secenekler": ["KDV", "Gelir Vergisi", "Kurumlar Vergisi", "Emlak Vergisi", "MTV"], "cevap": "KDV"},
        {"soru": "Vergi Usul Kanunu'na göre defter saklama süresi kaç yıldır?", "secenekler": ["5 Yıl", "10 Yıl", "3 Yıl", "1 Yıl", "20 Yıl"], "cevap": "5 Yıl"},
        {"soru": "Kurumlar Vergisi oranı (2024) yaklaşık kaçtır?", "secenekler": ["%25", "%10", "%50", "%1", "%5"], "cevap": "%25"},
        {"soru": "Muhtasar Beyanname ile ne beyan edilir?", "secenekler": ["Kesilen vergiler (Stopaj)", "KDV", "Yıllık gelir", "Emlak vergisi", "MTV"], "cevap": "Kesilen vergiler (Stopaj)"},
        {"soru": "Geçici vergi dönemleri kaçar aylıktır?", "secenekler": ["3 Ay", "1 Ay", "6 Ay", "12 Ay", "9 Ay"], "cevap": "3 Ay"},
        {"soru": "Verginin üzerinden hesaplandığı değere ne denir?", "secenekler": ["Matrah", "Tarife", "Oran", "Ceza", "Zam"], "cevap": "Matrah"},
        {"soru": "Özel Tüketim Vergisi (ÖTV) hangi mallardan alınır?", "secenekler": ["Lüks ve sağlığa zararlı mallardan", "Ekmekten", "Sudan", "İlaçtan", "Kitaptan"], "cevap": "Lüks ve sağlığa zararlı mallardan"}
    ],
    "11-İş ve Sosyal Güvenlik Hukuku": [
        {"soru": "İş sözleşmesini fesheden tarafın önceden bildirmesi gereken süreye ne denir?", "secenekler": ["İhbar Süresi", "Kıdem Süresi", "Deneme Süresi", "İzin Süresi", "Mola Süresi"], "cevap": "İhbar Süresi"},
        {"soru": "En az bir yıl çalışan işçiye işten çıkarıldığında ödenen tazminat nedir?", "secenekler": ["Kıdem Tazminatı", "İhbar Tazminatı", "Kötü Niyet Tazminatı", "Sendika Tazminatı", "Yol Tazminatı"], "cevap": "Kıdem Tazminatı"},
        {"soru": "Haftalık yasal çalışma saati kaç saattir?", "secenekler": ["45 Saat", "40 Saat", "50 Saat", "60 Saat", "30 Saat"], "cevap": "45 Saat"},
        {"soru": "SGK'da 4/a statüsü kimleri kapsar?", "secenekler": ["Hizmet akdiyle çalışanları (İşçiler)", "Bağ-Kurluları", "Memurları", "Çiftçileri", "Esnafı"], "cevap": "Hizmet akdiyle çalışanları (İşçiler)"},
        {"soru": "Yıllık ücretli izin hakkı için en az ne kadar çalışmak gerekir?", "secenekler": ["1 Yıl", "6 Ay", "3 Ay", "1 Ay", "5 Yıl"], "cevap": "1 Yıl"},
        {"soru": "İş kazası bildirim süresi kaç iş günüdür?", "secenekler": ["3 İş Günü", "5 İş Günü", "10 İş Günü", "1 Ay", "Bildirilmez"], "cevap": "3 İş Günü"},
        {"soru": "Asgari ücreti kim belirler?", "secenekler": ["Asgari Ücret Tespit Komisyonu", "İşveren", "İşçi", "Sendika", "Belediye"], "cevap": "Asgari Ücret Tespit Komisyonu"},
        {"soru": "4857 sayılı kanun hangi kanundur?", "secenekler": ["İş Kanunu", "Vergi Kanunu", "Ticaret Kanunu", "Medeni Kanun", "Ceza Kanunu"], "cevap": "İş Kanunu"},
        {"soru": "Fazla çalışma ücreti normal ücrete göre yüzde kaç zamlı ödenir?", "secenekler": ["%50", "%25", "%100", "%10", "%75"], "cevap": "%50"},
        {"soru": "Sendika kurmak için izin almaya gerek var mıdır?", "secenekler": ["Hayır, izin almaya gerek yoktur", "Evet, Valilikten izin alınır", "Evet, Bakanlıktan izin alınır", "Evet, İşverenden izin alınır", "Evet, Belediyeden izin alınır"], "cevap": "Hayır, izin almaya gerek yoktur"}
    ],
    
    # --- 12. SINIF ---
    "12-Dış Ticaret": [
        {"soru": "İhracat nedir?", "secenekler": ["Yurt dışına mal satmak", "Yurt dışından mal almak", "Üretim yapmak", "Vergi ödemek", "Depolama"], "cevap": "Yurt dışına mal satmak"},
        {"soru": "FOB teslim şekli ne anlama gelir?", "secenekler": ["Gemi güvertesinde teslim", "Fabrikada teslim", "Gümrükte teslim", "Sigorta dahil teslim", "Kapıda ödeme"], "cevap": "Gemi güvertesinde teslim"},
        {"soru": "Gümrük vergisi kime ödenir?", "secenekler": ["Gümrük İdaresine", "Belediyeye", "Satıcıya", "Alıcıya", "Nakliyeciye"], "cevap": "Gümrük İdaresine"},
        {"soru": "Akreditif nedir?", "secenekler": ["Banka garantili ödeme yöntemi", "Nakit ödeme", "Çek", "Senet", "Veresiye"], "cevap": "Banka garantili ödeme yöntemi"},
        {"soru": "İthalat nedir?", "secenekler": ["Yurt dışından mal almak", "Yurt dışına mal satmak", "Mal üretmek", "Hizmet vermek", "Yatırım yapmak"], "cevap": "Yurt dışından mal almak"},
        {"soru": "Dış ticarette kullanılan belge hangisidir?", "secenekler": ["Gümrük Beyannamesi", "Perakende Fiş", "Gider Pusulası", "Adisyon", "Reçete"], "cevap": "Gümrük Beyannamesi"},
        {"soru": "CIF teslim şeklinde sigortayı kim öder?", "secenekler": ["Satıcı", "Alıcı", "Nakliyeci", "Gümrük", "Devlet"], "cevap": "Satıcı"},
        {"soru": "Serbest bölgelerin temel amacı nedir?", "secenekler": ["İhracatı artırmak", "İthalatı artırmak", "Vergi toplamak", "Turizm yapmak", "Konut yapmak"], "cevap": "İhracatı artırmak"},
        {"soru": "Damping nedir?", "secenekler": ["Malı maliyetinin altında satmak", "Pahalı satmak", "Reklam yapmak", "Kaliteli üretmek", "Stoklamak"], "cevap": "Malı maliyetinin altında satmak"},
        {"soru": "Menşe şahadetnamesi neyi gösterir?", "secenekler": ["Malın üretildiği ülkeyi", "Malın fiyatını", "Malın ağırlığını", "Malın sahibini", "Malın rengini"], "cevap": "Malın üretildiği ülkeyi"}
    ],
    "12-Kooperatifçilik": [
        {"soru": "Kooperatiflerin temel amacı nedir?", "secenekler": ["Ortakların ekonomik menfaatlerini korumak", "Kar maksimizasyonu", "Rakip firmaları yok etmek", "Vergi vermemek", "Siyaset yapmak"], "cevap": "Ortakların ekonomik menfaatlerini korumak"},
        {"soru": "Kooperatif en az kaç kişiyle kurulur?", "secenekler": ["7", "5", "3", "10", "2"], "cevap": "7"},
        {"soru": "Kooperatiflerde her ortağın kaç oy hakkı vardır?", "secenekler": ["1 Oy", "Sermayesi kadar", "Kıdemi kadar", "Hisse sayısı kadar", "Yönetim belirler"], "cevap": "1 Oy"},
        {"soru": "Risturn nedir?", "secenekler": ["Kooperatif kar payı dağıtımı", "Zarar", "Gider", "Vergi", "Aidat"], "cevap": "Kooperatif kar payı dağıtımı"},
        {"soru": "Kooperatifin en yetkili organı hangisidir?", "secenekler": ["Genel Kurul", "Yönetim Kurulu", "Denetim Kurulu", "Başkan", "Müdür"], "cevap": "Genel Kurul"},
        {"soru": "Kooperatif ana sözleşmesi nereye tescil edilir?", "secenekler": ["Ticaret Sicili", "Belediye", "Muhtarlık", "Maliye", "Banka"], "cevap": "Ticaret Sicili"},
        {"soru": "Aşağıdakilerden hangisi bir kooperatif türüdür?", "secenekler": ["Yapı Kooperatifi", "Anonim Şirket", "Limited Şirket", "Kolektif Şirket", "Komandit Şirket"], "cevap": "Yapı Kooperatifi"},
        {"soru": "Kooperatiflerde denetimi kim yapar?", "secenekler": ["Denetim Kurulu", "Yönetim Kurulu", "Başkan", "Muhasebeci", "Bekçi"], "cevap": "Denetim Kurulu"},
        {"soru": "Kooperatif ortaklığından çıkmak mümkün müdür?", "secenekler": ["Evet, mümkündür", "Hayır, yasaktır", "Sadece ölünce", "Yönetim izin verirse", "Devlet izin verirse"], "cevap": "Evet, mümkündür"},
        {"soru": "Kooperatifler hangi kanuna tabidir?", "secenekler": ["Kooperatifler Kanunu", "Ceza Kanunu", "Medeni Kanun", "İş Kanunu", "Vergi Kanunu"], "cevap": "Kooperatifler Kanunu"}
    ],
    "12-Ahilik Kültürü": [
        {"soru": "Ahilik teşkilatının kurucusu kimdir?", "secenekler": ["Ahi Evran", "Mevlana", "Yunus Emre", "Hacı Bektaş", "Nasreddin Hoca"], "cevap": "Ahi Evran"},
        {"soru": "Ahilikte esnafın uyması gereken kuralların yazılı olduğu eser nedir?", "secenekler": ["Fütüvvetname", "Mesnevi", "Divan", "Nutuk", "Siyasetname"], "cevap": "Fütüvvetname"},
        {"soru": "Ahilikte eğitim sistemi nasıldır?", "secenekler": ["Usta-Çırak ilişkisi", "Okul eğitimi", "Uzaktan eğitim", "Sınavla", "Parayla"], "cevap": "Usta-Çırak ilişkisi"},
        {"soru": "Pabucu dama atılmak deyimi hangi teşkilattan gelir?", "secenekler": ["Ahilik", "Yeniçeri", "Enderun", "Medrese", "Lonca"], "cevap": "Ahilik"},
        {"soru": "Ahilikte kalfalıktan ustalığa geçiş törenine ne denir?", "secenekler": ["Şed Kuşanma", "Mezuniyet", "Diploma", "İcazet", "Terfi"], "cevap": "Şed Kuşanma"},
        {"soru": "Ahiliğin temel ilkesi nedir?", "secenekler": ["Eline, beline, diline sahip ol", "Çok kazan", "Rakibini ez", "Sadece kendini düşün", "Hile yap"], "cevap": "Eline, beline, diline sahip ol"},
        {"soru": "Ahilik teşkilatının merkezi neresidir?", "secenekler": ["Kırşehir", "İstanbul", "Ankara", "Konya", "Bursa"], "cevap": "Kırşehir"},
        {"soru": "Ahilikte 'Yamak' kime denir?", "secenekler": ["Çıraklığa yeni başlayan", "Usta", "Kalfa", "Başkan", "Müşteri"], "cevap": "Çıraklığa yeni başlayan"},
        {"soru": "Ahilikte kalite kontrolü yapan kişiye ne denir?", "secenekler": ["Kethüda", "Zabıt", "Polis", "Hakim", "Kadı"], "cevap": "Kethüda"},
        {"soru": "Ahilik günümüzdeki hangi kuruluşun temelidir?", "secenekler": ["Esnaf ve Sanatkarlar Odası", "Belediye", "Maliye", "Banka", "Okul"], "cevap": "Esnaf ve Sanatkarlar Odası"}
    ]
}

# --- AI AYARLARI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def yapay_zeka_soru_uret(sinif, ders):
    ai_sorulari = []
    
    # Derse özel anahtarı oluştur (Örn: "9-Temel Muhasebe")
    sinif_no = sinif.split(".")[0]
    ders_key = f"{sinif_no}-{ders}" 
    
    # Konu Havuzundan Ders İçeriğini Al
    konu_metni = KONU_HAVUZU.get(ders_key, "Müfredat Konuları")
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Rolün: Lise Öğretmeni. Ders: {ders} ({sinif}).
        Müfredat Konuları: {konu_metni}
        
        GÖREV: Yukarıdaki konulardan TAM 10 ADET test sorusu üret.
        
        KURALLAR:
        1. SADECE {ders} dersinin konularından sor. ASLA BAŞKA DERS SORMA.
        2. {ders} dersi için {konu_metni} dışına çıkma.
        3. Her sorunun 5 şıkkı (A,B,C,D,E) olsun.
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
    if len(ai_sorulari) < 10:
        # 1. Tam eşleşen yedeği bul
        ozel_yedek = YEDEK_DEPO.get(ders_key, [])
        
        # 2. Bulamazsa sadece ders adına bak
        if not ozel_yedek:
            for key, val in YEDEK_DEPO.items():
                if ders in key or key in ders:
                    ozel_yedek = val
                    break
        
        # 3. Yedeği karıştır ve ekle
        if ozel_yedek:
            eksik = 10 - len(ai_sorulari)
            random.shuffle(ozel_yedek)
            while len(ozel_yedek) < eksik: # Yedek azsa çoğalt
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
