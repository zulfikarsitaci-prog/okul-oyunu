import streamlit as st
import google.generativeai as genai
import json
import time
import random
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Bağarası Hibrit Eğitim Merkezi", page_icon="🎓", layout="centered")

# --- TASARIM: IHLAMUR YEŞİLİ & SARI KİREMİT ---
st.markdown("""
    <style>
    /* 1. Arka Plan: Ihlamur Yeşili */
    .stApp {
        background-color: #F0F4C3 !important; 
    }
    
    /* 2. Yazı Renkleri: Siyah ve Okunaklı */
    h1, h2, h3, h4, h5, h6, p, div, span, label, li, .stMarkdown {
        color: #212121 !important;
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* 3. Butonlar: Sarı Kiremit / Turuncu Tonları */
    .stButton>button { 
        width: 100%; 
        border-radius: 12px; 
        min-height: 4.5em; 
        font-weight: 700; 
        background-color: #FF7043 !important; /* Kiremit Rengi */
        color: #FFFFFF !important; /* Yazı Beyaz */
        border: 2px solid #D84315 !important; 
        white-space: pre-wrap; 
        padding: 10px;
        transition: transform 0.2s;
    }
    
    .stButton>button:hover { 
        background-color: #FF5722 !important; 
        transform: scale(1.02);
        color: #FFFFFF !important;
    }
    
    /* 4. Seçim Kutuları */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important; 
        color: #000000 !important; 
        border: 2px solid #FF7043 !important;
    }
    
    /* 5. Soru Kartı */
    .big-font { 
        font-size: 22px !important; 
        font-weight: 700; 
        color: #000000 !important; 
        margin-bottom: 25px; 
        padding: 20px; 
        background-color: rgba(255,255,255,0.7); 
        border-left: 8px solid #FF7043;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* 6. Sidebar */
    [data-testid="stSidebar"] {
        background-color: #DCEDC8 !important; 
        border-right: 2px solid #AED581;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 1. VERİ HAVUZLARI
# ==============================================================================

# A) MESLEK DERSLERİ GRUPLAMASI
MESLEK_GRUPLARI = {
    "9. Sınıf Meslek": ["Temel Muhasebe", "Mesleki Matematik", "Ofis Uygulamaları", "Mesleki Gelişim"],
    "10. Sınıf Meslek": ["Genel Muhasebe", "Temel Hukuk", "Ekonomi", "Klavye Teknikleri"],
    "11. Sınıf Meslek": ["Bilgisayarlı Muhasebe", "Maliyet Muhasebesi", "Vergi ve Beyannameler", "Şirketler Muhasebesi", "İş Hukuku"],
    "12. Sınıf Meslek": ["Dış Ticaret", "Kooperatifçilik", "Ahilik Kültürü"]
}

# B) YEDEK DEPO - MESLEK (ÖZET)
YEDEK_MESLEK = {
    "9. Sınıf Meslek": [
        {"soru": "Çiftçiden ürün alırken düzenlenen belge hangisidir?", "secenekler": ["Müstahsil Makbuzu", "Fatura", "Gider Pusulası", "İrsaliye", "Fiş"], "cevap": "Müstahsil Makbuzu"},
        {"soru": "KDV hariç 500 TL olan malın %20 KDV tutarı kaçtır?", "secenekler": ["100 TL", "50 TL", "20 TL", "120 TL", "80 TL"], "cevap": "100 TL"},
        {"soru": "Excel'de toplama formülü nedir?", "secenekler": ["=TOPLA()", "=ÇIKAR()", "=SAY()", "=EĞER()", "=ORTALAMA()"], "cevap": "=TOPLA()"},
        {"soru": "Ahiliğin kurucusu kimdir?", "secenekler": ["Ahi Evran", "Mevlana", "Yunus Emre", "Hacı Bektaş", "Kaşgarlı Mahmut"], "cevap": "Ahi Evran"},
        {"soru": "Maliyet fiyatı üzerine kar eklenince ne bulunur?", "secenekler": ["Satış Fiyatı", "Zarar", "Gider", "İskonto", "Ciro"], "cevap": "Satış Fiyatı"},
        {"soru": "Ticari defterlerin saklama süresi kaç yıldır?", "secenekler": ["5 Yıl", "10 Yıl", "1 Yıl", "3 Yıl", "20 Yıl"], "cevap": "5 Yıl"},
        {"soru": "Vergi levhası nereden alınır?", "secenekler": ["GİB (İnternet Vergi Dairesi)", "Belediye", "Muhtarlık", "Noter", "Valilik"], "cevap": "GİB (İnternet Vergi Dairesi)"},
        {"soru": "Word programında metni kalın yapmak için hangi harf kullanılır?", "secenekler": ["K", "T", "A", "Ç", "S"], "cevap": "K"},
        {"soru": "Etkili iletişimde en önemli unsur nedir?", "secenekler": ["Dinlemek", "Konuşmak", "Bağırmak", "Gülmek", "Susmak"], "cevap": "Dinlemek"},
        {"soru": "İşletme defterinin sol tarafına ne yazılır?", "secenekler": ["Giderler", "Gelirler", "Karlar", "Satışlar", "Alacaklar"], "cevap": "Giderler"}
    ],
    "10. Sınıf Meslek": [
        {"soru": "Bilanço temel denkliği hangisidir?", "secenekler": ["Varlıklar = Kaynaklar", "Gelir = Gider", "Aktif = Pasif - Sermaye", "Kasa = Banka", "Borç = Alacak"], "cevap": "Varlıklar = Kaynaklar"},
        {"soru": "Hak ehliyeti ne zaman başlar?", "secenekler": ["Tam ve sağ doğumla", "18 yaşla", "Evlenince", "Okula başlayınca", "İşe girince"], "cevap": "Tam ve sağ doğumla"},
        {"soru": "Fiyatlar genel seviyesinin sürekli artmasına ne denir?", "secenekler": ["Enflasyon", "Devalüasyon", "Resesyon", "Deflasyon", "Kriz"], "cevap": "Enflasyon"},
        {"soru": "100 Kasa hesabı nasıl çalışır?", "secenekler": ["Girişler Borç, Çıkışlar Alacak", "Girişler Alacak, Çıkışlar Borç", "Hep Alacaklı", "Hep Borçlu", "Çalışmaz"], "cevap": "Girişler Borç, Çıkışlar Alacak"},
        {"soru": "Tacir kime denir?", "secenekler": ["Ticari işletmeyi işleten", "Memur", "İşçi", "Öğrenci", "Emekli"], "cevap": "Ticari işletmeyi işleten"},
        {"soru": "Mizan nedir?", "secenekler": ["Hesapların borç/alacak toplamlarını gösteren çizelge", "Mali durum tablosu", "Kar zarar tablosu", "Fatura listesi", "Vergi beyannamesi"], "cevap": "Hesapların borç/alacak toplamlarını gösteren çizelge"},
        {"soru": "Çek üzerindeki vadeye ne ad verilir?", "secenekler": ["Keşide Tarihi", "Vade", "Tanzim", "Ciro", "Aval"], "cevap": "Keşide Tarihi"},
        {"soru": "Merkez Bankasının temel görevi nedir?", "secenekler": ["Fiyat istikrarını sağlamak", "Kredi vermek", "Maaş dağıtmak", "Vergi toplamak", "Yol yapmak"], "cevap": "Fiyat istikrarını sağlamak"},
        {"soru": "F klavyede sol elin işaret parmağı hangi tuşta durur?", "secenekler": ["A", "K", "E", "M", "Ü"], "cevap": "A"},
        {"soru": "Borcun unsurları nelerdir?", "secenekler": ["Alacaklı, Borçlu, Edim", "Hakim, Savcı, Avukat", "Para, Mal, Hizmet", "Evrak, Kayıt, Defter", "Banka, Kasa, Çek"], "cevap": "Alacaklı, Borçlu, Edim"}
    ],
    "11. Sınıf Meslek": [
        {"soru": "KDV beyannamesi ne zaman verilir?", "secenekler": ["Takip eden ayın 28'i", "Yıl sonunda", "Her hafta", "Günlük", "3 ayda bir"], "cevap": "Takip eden ayın 28'i"},
        {"soru": "7/A seçeneğinde Direkt İlk Madde ve Malzeme Giderleri kodu nedir?", "secenekler": ["710", "720", "730", "740", "750"], "cevap": "710"},
        {"soru": "Bilgisayarlı muhasebede 'Fiş Kaydı' nereden yapılır?", "secenekler": ["Muhasebe Modülü", "Stok Modülü", "Cari Modülü", "Çek/Senet", "Fatura"], "cevap": "Muhasebe Modülü"},
        {"soru": "Kıdem tazminatı alabilmek için en az ne kadar çalışmak gerekir?", "secenekler": ["1 Yıl", "6 Ay", "3 Ay", "1 Ay", "5 Yıl"], "cevap": "1 Yıl"},
        {"soru": "Kurumlar Vergisi oranı (2024) yaklaşık kaçtır?", "secenekler": ["%25", "%10", "%50", "%1", "%5"], "cevap": "%25"},
        {"soru": "Şirket kuruluşunda sermaye taahhüdü hangi hesaba borç yazılır?", "secenekler": ["501 Ödenmemiş Sermaye", "500 Sermaye", "100 Kasa", "102 Bankalar", "320 Satıcılar"], "cevap": "501 Ödenmemiş Sermaye"},
        {"soru": "150 İlk Madde ve Malzeme hesabı hangi gruptadır?", "secenekler": ["Stoklar", "Hazır Değerler", "Duran Varlıklar", "Maliyet Hesapları", "Gelir Hesapları"], "cevap": "Stoklar"},
        {"soru": "Muhtasar Beyanname ile ne beyan edilir?", "secenekler": ["Stopaj (Kesinti) Vergileri", "KDV", "Yıllık Gelir", "Emlak Vergisi", "MTV"], "cevap": "Stopaj (Kesinti) Vergileri"},
        {"soru": "İş kazası bildirim süresi kaç gündür?", "secenekler": ["3 İş Günü", "10 Gün", "1 Ay", "Hemen", "1 Yıl"], "cevap": "3 İş Günü"},
        {"soru": "Anonim şirketlerin asgari sermayesi ne kadardır (2024)?", "secenekler": ["250.000 TL", "50.000 TL", "10.000 TL", "1 Milyon TL", "500.000 TL"], "cevap": "250.000 TL"}
    ],
    "12. Sınıf Meslek": [
        {"soru": "İhracat nedir?", "secenekler": ["Yurt dışına mal satmak", "Yurt dışından mal almak", "Üretim yapmak", "Vergi ödemek", "Depolama"], "cevap": "Yurt dışına mal satmak"},
        {"soru": "Kooperatiflerin temel amacı nedir?", "secenekler": ["Ortakların ekonomik menfaatlerini korumak", "Kar maksimizasyonu", "Rakip firmaları yok etmek", "Vergi vermemek", "Siyaset yapmak"], "cevap": "Ortakların ekonomik menfaatlerini korumak"},
        {"soru": "FOB teslim şekli ne anlama gelir?", "secenekler": ["Gemi güvertesinde teslim", "Fabrikada teslim", "Gümrükte teslim", "Sigorta dahil teslim", "Kapıda ödeme"], "cevap": "Gemi güvertesinde teslim"},
        {"soru": "Ahilikte kalfalıktan ustalığa geçiş törenine ne denir?", "secenekler": ["Şed Kuşanma", "Mezuniyet", "Diploma", "İcazet", "Terfi"], "cevap": "Şed Kuşanma"},
        {"soru": "Gümrük vergisi kime ödenir?", "secenekler": ["Gümrük İdaresine", "Belediyeye", "Satıcıya", "Alıcıya", "Nakliyeciye"], "cevap": "Gümrük İdaresine"},
        {"soru": "Akreditif nedir?", "secenekler": ["Banka garantili ödeme", "Nakit ödeme", "Çek", "Senet", "Veresiye"], "cevap": "Banka garantili ödeme"},
        {"soru": "Risturn nedir?", "secenekler": ["Kooperatif kar payı", "Vergi iadesi", "İhracat teşviki", "Gümrük cezası", "Aidat"], "cevap": "Kooperatif kar payı"},
        {"soru": "Serbest bölgelerin amacı nedir?", "secenekler": ["İhracatı artırmak", "Turizmi canlandırmak", "Konut yapmak", "Vergi toplamak", "Nüfusu artırmak"], "cevap": "İhracatı artırmak"},
        {"soru": "Dış ticarette kullanılan belge hangisidir?", "secenekler": ["Gümrük Beyannamesi", "Perakende Fiş", "Gider Pusulası", "Adisyon", "Reçete"], "cevap": "Gümrük Beyannamesi"},
        {"soru": "Kooperatif en az kaç kişiyle kurulur?", "secenekler": ["7", "5", "3", "10", "20"], "cevap": "7"}
    ]
}

# C) YEDEK DEPO - TYT (GENİŞLETİLMİŞ VE TEKRARSIZ)
# Her ders için 15 adet soru eklenmiştir.
YEDEK_TYT = {
    "Tarih": [
        {"soru": "Milli Mücadele'nin gerekçesi, amacı ve yöntemi ilk kez nerede belirtilmiştir?", "secenekler": ["Amasya Genelgesi", "Erzurum Kongresi", "Sivas Kongresi", "Misak-ı Milli", "Havza Genelgesi"], "cevap": "Amasya Genelgesi"},
        {"soru": "Mustafa Kemal'e 'Atatürk' soyadı hangi yıl verilmiştir?", "secenekler": ["1934", "1923", "1938", "1920", "1930"], "cevap": "1934"},
        {"soru": "İlk Türk devletlerinde devlet işlerinin görüşüldüğü meclise ne ad verilir?", "secenekler": ["Kurultay (Toy)", "Divan", "Pankuş", "Senato", "Meclis"], "cevap": "Kurultay (Toy)"},
        {"soru": "Osmanlı Devleti'nde ilk anayasa hangisidir?", "secenekler": ["Kanun-i Esasi", "Sened-i İttifak", "Tanzimat Fermanı", "Islahat Fermanı", "Teşkilat-ı Esasiye"], "cevap": "Kanun-i Esasi"},
        {"soru": "İstanbul'un fethi ile hangi çağ kapanıp hangi çağ başlamıştır?", "secenekler": ["Orta Çağ - Yeni Çağ", "İlk Çağ - Orta Çağ", "Yeni Çağ - Yakın Çağ", "Karanlık Çağ - İlk Çağ", "Yontma Taş - Cilalı Taş"], "cevap": "Orta Çağ - Yeni Çağ"},
        {"soru": "Malazgirt Meydan Muharebesi hangi tarihte yapılmıştır?", "secenekler": ["1071", "1453", "1299", "1923", "1919"], "cevap": "1071"},
        {"soru": "Lozan Barış Antlaşması hangi savaştan sonra imzalanmıştır?", "secenekler": ["Kurtuluş Savaşı", "I. Dünya Savaşı", "Balkan Savaşı", "Trablusgarp Savaşı", "II. Dünya Savaşı"], "cevap": "Kurtuluş Savaşı"},
        {"soru": "Osmanlı Devleti'nde 'Devşirme Sistemi' ile asker yetiştiren ocak hangisidir?", "secenekler": ["Yeniçeri Ocağı", "Tımarlı Sipahi", "Akıncılar", "Leventler", "Azaplar"], "cevap": "Yeniçeri Ocağı"},
        {"soru": "Cumhuriyet hangi tarihte ilan edilmiştir?", "secenekler": ["29 Ekim 1923", "23 Nisan 1920", "19 Mayıs 1919", "30 Ağustos 1922", "9 Eylül 1922"], "cevap": "29 Ekim 1923"},
        {"soru": "Kavimler Göçü sonucunda hangi devlet ikiye ayrılmıştır?", "secenekler": ["Roma İmparatorluğu", "Osmanlı Devleti", "Büyük İskender", "Pers İmparatorluğu", "Çin"], "cevap": "Roma İmparatorluğu"},
        {"soru": "Hangi padişah döneminde Osmanlı Devleti 'İmparatorluk' özelliği kazanmıştır?", "secenekler": ["Fatih Sultan Mehmet", "Yavuz Sultan Selim", "Kanuni Sultan Süleyman", "Osman Bey", "Orhan Bey"], "cevap": "Fatih Sultan Mehmet"},
        {"soru": "Misak-ı Milli kararları nerede kabul edilmiştir?", "secenekler": ["Son Osmanlı Mebusan Meclisi", "TBMM", "Sivas Kongresi", "Erzurum Kongresi", "Lozan"], "cevap": "Son Osmanlı Mebusan Meclisi"},
        {"soru": "Düzenli ordunun kazandığı ilk zafer hangisidir?", "secenekler": ["I. İnönü", "Sakarya", "Büyük Taarruz", "Kütahya-Eskişehir", "Gediz"], "cevap": "I. İnönü"},
        {"soru": "Hangi Atatürk ilkesi, din ve devlet işlerinin birbirinden ayrılmasını esas alır?", "secenekler": ["Laiklik", "Cumhuriyetçilik", "Milliyetçilik", "Halkçılık", "Devletçilik"], "cevap": "Laiklik"},
        {"soru": "Osmanlı'da Divan-ı Hümayun'a başkanlık eden devlet görevlisi (Padişah yoksa) kimdir?", "secenekler": ["Sadrazam", "Nişancı", "Defterdar", "Kazasker", "Şeyhülislam"], "cevap": "Sadrazam"}
    ],
    "Coğrafya": [
        {"soru": "Türkiye'nin matematik konumu nedir?", "secenekler": ["36-42 Kuzey, 26-45 Doğu", "36-42 Güney, 26-45 Batı", "26-45 Kuzey, 36-42 Doğu", "10-20 Kuzey, 30-40 Doğu", "Ekvator üzerinde"], "cevap": "36-42 Kuzey, 26-45 Doğu"},
        {"soru": "Aşağıdakilerden hangisi bir doğal afettir?", "secenekler": ["Deprem", "Trafik Kazası", "Savaş", "Göç", "Sanayileşme"], "cevap": "Deprem"},
        {"soru": "Türkiye'de en çok yağış alan bölge hangisidir?", "secenekler": ["Karadeniz", "Akdeniz", "Ege", "İç Anadolu", "Güneydoğu Anadolu"], "cevap": "Karadeniz"},
        {"soru": "Yerel saat farkları neden oluşur?", "secenekler": ["Dünya'nın kendi ekseni etrafında dönmesi", "Dünya'nın Güneş etrafında dönmesi", "Eksen eğikliği", "Mevsimler", "Ay'ın hareketleri"], "cevap": "Dünya'nın kendi ekseni etrafında dönmesi"},
        {"soru": "Aşağıdakilerden hangisi karstik bir şekildir?", "secenekler": ["Mağara", "Delta", "Hörgüç Kaya", "Kumul", "Fiyord"], "cevap": "Mağara"},
        {"soru": "Nüfus yoğunluğunun en fazla olduğu bölgemiz hangisidir?", "secenekler": ["Marmara", "Doğu Anadolu", "Karadeniz", "Akdeniz", "Güneydoğu Anadolu"], "cevap": "Marmara"},
        {"soru": "Akdeniz ikliminin bitki örtüsü nedir?", "secenekler": ["Maki", "Bozkır", "Orman", "Tundra", "Savan"], "cevap": "Maki"},
        {"soru": "Türkiye'de heyelan olaylarına en çok nerede rastlanır?", "secenekler": ["Karadeniz Bölgesi", "İç Anadolu Bölgesi", "Ege Bölgesi", "Marmara Bölgesi", "Güneydoğu Anadolu"], "cevap": "Karadeniz Bölgesi"},
        {"soru": "Aşağıdakilerden hangisi beşeri bir unsurdur?", "secenekler": ["Baraj", "Dağ", "Nehir", "Ova", "Göl"], "cevap": "Baraj"},
        {"soru": "Haritada bir noktanın Ekvator'a olan uzaklığının açı cinsinden değerine ne denir?", "secenekler": ["Enlem", "Boylam", "Ölçek", "Rakım", "Eğim"], "cevap": "Enlem"},
        {"soru": "Türkiye'de en fazla çıkarılan madenlerden biri hangisidir?", "secenekler": ["Bor", "Elmas", "Platin", "Uranyum", "Titanyum"], "cevap": "Bor"},
        {"soru": "Rüzgarın aşındırma ve biriktirme şekillerine en çok nerede rastlanır?", "secenekler": ["Çöl ve kurak bölgelerde", "Ormanlık alanlarda", "Kutuplarda", "Okyanus kıyılarında", "Dağ tepelerinde"], "cevap": "Çöl ve kurak bölgelerde"},
        {"soru": "İzohips haritalarında çizgilerin sıklaştığı yerlerde ne fazladır?", "secenekler": ["Eğim", "Sıcaklık", "Yağış", "Nüfus", "Basınç"], "cevap": "Eğim"},
        {"soru": "Aşağıdaki denizlerden hangisi Türkiye'yi çevreler?", "secenekler": ["Karadeniz, Akdeniz, Ege", "Hazar, Aral, Lut", "Kızıldeniz, Umman, Basra", "Baltık, Adriyatik, Manş", "Bering, Ohotsk, Sarı"], "cevap": "Karadeniz, Akdeniz, Ege"},
        {"soru": "Dünya'nın şekli nasıldır?", "secenekler": ["Geoid (Kutuplardan basık)", "Tam küre", "Düz tepsi", "Küp", "Silindir"], "cevap": "Geoid (Kutuplardan basık)"}
    ],
    "Matematik": [
        {"soru": "Bir sayının 3 katının 5 eksiği 16 ise bu sayı kaçtır?", "secenekler": ["7", "6", "8", "5", "9"], "cevap": "7"},
        {"soru": "Ardışık 3 tek sayının toplamı 33 ise en büyüğü kaçtır?", "secenekler": ["13", "11", "9", "15", "17"], "cevap": "13"},
        {"soru": "Bir sınıftaki öğrencilerin %40'ı kızdır. Sınıfta 12 erkek varsa sınıf mevcudu kaçtır?", "secenekler": ["20", "25", "30", "15", "18"], "cevap": "20"},
        {"soru": "3x - 5 = 10 ise x kaçtır?", "secenekler": ["5", "3", "4", "6", "2"], "cevap": "5"},
        {"soru": "Kök 144 dışarı nasıl çıkar?", "secenekler": ["12", "14", "10", "11", "13"], "cevap": "12"},
        {"soru": "Bir araç 60 km hızla 3 saatte kaç km yol gider?", "secenekler": ["180", "120", "200", "150", "240"], "cevap": "180"},
        {"soru": "Hangi sayının karesi 81'dir?", "secenekler": ["9", "8", "7", "6", "5"], "cevap": "9"},
        {"soru": "2 üssü 5 kaçtır?", "secenekler": ["32", "16", "64", "25", "10"], "cevap": "32"},
        {"soru": "Bir üçgenin iç açıları toplamı kaç derecedir?", "secenekler": ["180", "360", "90", "100", "270"], "cevap": "180"},
        {"soru": "Ali 10, Veli 15 yaşındadır. 5 yıl sonra yaşları toplamı kaç olur?", "secenekler": ["35", "30", "25", "40", "20"], "cevap": "35"},
        {"soru": "Bir manavda elmanın kilosu 5 TL. 4 kilo elma alan biri 50 TL verirse ne kadar para üstü alır?", "secenekler": ["30 TL", "20 TL", "25 TL", "35 TL", "10 TL"], "cevap": "30 TL"},
        {"soru": "En küçük asal sayı kaçtır?", "secenekler": ["2", "1", "3", "0", "5"], "cevap": "2"},
        {"soru": "Aşağıdakilerden hangisi irrasyonel bir sayıdır?", "secenekler": ["Pi sayısı", "5", "1/2", "0", "-10"], "cevap": "Pi sayısı"},
        {"soru": "Mutlak değer içinde -7 dışarı nasıl çıkar?", "secenekler": ["7", "-7", "0", "1/7", "14"], "cevap": "7"},
        {"soru": "f(x) = 2x + 1 ise f(3) kaçtır?", "secenekler": ["7", "6", "5", "8", "9"], "cevap": "7"}
    ],
    "Türkçe": [
        {"soru": "Aşağıdaki cümlelerin hangisinde 'ünsüz benzeşmesi' vardır?", "secenekler": ["Kitapçı", "Masa", "Kalem", "Araba", "Silgi"], "cevap": "Kitapçı"},
        {"soru": "Paragrafta 'yakınmak' ne anlama gelir?", "secenekler": ["Şikayet etmek", "Beğenmek", "Özlemek", "Kıskanmak", "Sevmek"], "cevap": "Şikayet etmek"},
        {"soru": "Hangi cümlede yazım yanlışı vardır?", "secenekler": ["Herşey çok güzel olacak.", "Bu akşam gelebilirim.", "Türkçe dersini seviyorum.", "Ankara'ya gittim.", "Kitap okumayı severim."], "cevap": "Herşey çok güzel olacak."},
        {"soru": "'Ağır' kelimesi hangi cümlede mecaz anlamda kullanılmıştır?", "secenekler": ["Çok ağır sözler söyledi.", "Bu çanta çok ağır.", "Ağır adımlarla yürüdü.", "Masa oldukça ağırdı.", "Taş yerinde ağırdır."], "cevap": "Çok ağır sözler söyledi."},
        {"soru": "Aşağıdakilerden hangisi bir 'Sıfat' (Ön ad) tır?", "secenekler": ["Kırmızı (Elma)", "Koşmak", "Ali", "Ben", "Hızlıca"], "cevap": "Kırmızı (Elma)"},
        {"soru": "Cümlenin öğelerinden hangisi işi yapanı bildirir?", "secenekler": ["Özne", "Yüklem", "Nesne", "Zarf Tümleci", "Dolaylı Tümleç"], "cevap": "Özne"},
        {"soru": "Hangisi bir noktalama işaretidir?", "secenekler": ["Virgül", "Harf", "Rakam", "Hece", "Kelime"], "cevap": "Virgül"},
        {"soru": "'Göz atmak' deyiminin anlamı nedir?", "secenekler": ["Şöyle bir bakıvermek", "Dikkatlice incelemek", "Gözünü kırpmak", "Gözü bozulmak", "Görmezden gelmek"], "cevap": "Şöyle bir bakıvermek"},
        {"soru": "Aşağıdaki kelimelerden hangisi türemiş kelimedir?", "secenekler": ["Simitçi", "Balık", "Ev", "Yol", "Su"], "cevap": "Simitçi"},
        {"soru": "Hangi cümlede 'karşılaştırma' yapılmıştır?", "secenekler": ["Ahmet, Mehmet'ten daha çalışkandır.", "Bugün hava çok güzel.", "Okula gidiyorum.", "Kitap okumayı severim.", "Akşam bize gel."], "cevap": "Ahmet, Mehmet'ten daha çalışkandır."},
        {"soru": "Hangisi eş sesli (sesteş) bir kelimedir?", "secenekler": ["Yüz", "Masa", "Bilgisayar", "Telefon", "Lamba"], "cevap": "Yüz"},
        {"soru": "'Büyük' kelimesinin zıt anlamlısı nedir?", "secenekler": ["Küçük", "İri", "Kocaman", "Dev", "Ufak"], "cevap": "Küçük"},
        {"soru": "Aşağıdakilerden hangisi kişi zamiridir?", "secenekler": ["Ben", "Kitap", "Güzel", "Koş", "Sarı"], "cevap": "Ben"},
        {"soru": "Hangi kelimenin yazımı doğrudur?", "secenekler": ["Yalnız", "Yanlız", "Yalnış", "Herkez", "Kirbit"], "cevap": "Yalnız"},
        {"soru": "Paragrafın ana düşüncesi nedir?", "secenekler": ["Yazarın asıl anlatmak istediği mesaj", "Giriş cümlesi", "Sonuç cümlesi", "Konu", "Başlık"], "cevap": "Yazarın asıl anlatmak istediği mesaj"}
    ],
    "Genel Deneme": [
        {"soru": "Milli Mücadelenin başlangıcı kabul edilen olay nedir?", "secenekler": ["19 Mayıs 1919 Samsun'a Çıkış", "TBMM'nin Açılışı", "Cumhuriyetin İlanı", "Sivas Kongresi", "Lozan Antlaşması"], "cevap": "19 Mayıs 1919 Samsun'a Çıkış"},
        {"soru": "Bir sınıftaki 20 öğrencinin %40'ı kız ise kaç erkek öğrenci vardır?", "secenekler": ["12", "8", "10", "14", "16"], "cevap": "12"},
        {"soru": "Türkiye'nin başkenti neresidir?", "secenekler": ["Ankara", "İstanbul", "İzmir", "Konya", "Bursa"], "cevap": "Ankara"},
        {"soru": "Su, kaç derecede kaynar?", "secenekler": ["100", "90", "50", "0", "120"], "cevap": "100"},
        {"soru": "İstiklal Marşı'mızın şairi kimdir?", "secenekler": ["Mehmet Akif Ersoy", "Namık Kemal", "Orhan Veli", "Nazım Hikmet", "Ziya Gökalp"], "cevap": "Mehmet Akif Ersoy"},
        {"soru": "Bir deste kalem kaç adettir?", "secenekler": ["10", "12", "20", "5", "100"], "cevap": "10"},
        {"soru": "Türkiye'nin en yüksek dağı hangisidir?", "secenekler": ["Ağrı Dağı", "Erciyes", "Uludağ", "Palandöken", "Toroslar"], "cevap": "Ağrı Dağı"},
        {"soru": "Hangisi bir yön değildir?", "secenekler": ["Yukarı", "Kuzey", "Güney", "Doğu", "Batı"], "cevap": "Yukarı"},
        {"soru": "İlk Cumhurbaşkanımız kimdir?", "secenekler": ["Mustafa Kemal Atatürk", "İsmet İnönü", "Celal Bayar", "Kenan Evren", "Turgut Özal"], "cevap": "Mustafa Kemal Atatürk"},
        {"soru": "Hangi renk ana renklerden biridir?", "secenekler": ["Kırmızı", "Yeşil", "Turuncu", "Mor", "Pembe"], "cevap": "Kırmızı"},
        {"soru": "Bir yıl kaç aydır?", "secenekler": ["12", "10", "6", "24", "30"], "cevap": "12"},
        {"soru": "Hangisi bir duyu organımızdır?", "secenekler": ["Göz", "Kalp", "Mide", "Akciğer", "Karaciğer"], "cevap": "Göz"},
        {"soru": "Futbol maçı kaç dakika sürer?", "secenekler": ["90", "45", "60", "100", "80"], "cevap": "90"},
        {"soru": "Alfabemizin ilk harfi nedir?", "secenekler": ["A", "B", "C", "Z", "K"], "cevap": "A"},
        {"soru": "Türkiye hangi kıtalarda yer alır?", "secenekler": ["Asya ve Avrupa", "Asya ve Afrika", "Avrupa ve Afrika", "Amerika ve Asya", "Sadece Asya"], "cevap": "Asya ve Avrupa"}
    ]
}

# --- AI AYARLARI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def soru_uret(kategori, alt_baslik):
    ai_sorulari = []
    
    # 1. AI ÇAĞRISI (ÖNCE BUNU DENE)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        if "Meslek" in kategori:
            konu_listesi = ", ".join(MESLEK_GRUPLARI.get(alt_baslik, []))
            prompt_ozel = f"Şu derslerden KARIŞIK sorular hazırla: {konu_listesi}"
        else:
            prompt_ozel = f"{alt_baslik} dersi için ÖSYM/TYT tarzı sorular hazırla."

        prompt = f"""
        Rol: Uzman Öğretmen.
        Görev: {prompt_ozel}
        Adet: 15 Soru.
        
        KURALLAR:
        1. Çıktı SADECE JSON.
        2. 5 Şıklı (A,B,C,D,E).
        3. Cevaplar rastgele.
        
        JSON: [ {{ "soru": "...", "secenekler": ["..."], "cevap": "..." }} ]
        """
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"): text = text.split("```")[1].strip()
        if text.startswith("json"): text = text[4:].strip()
        ai_sorulari = json.loads(text)
    except:
        ai_sorulari = []

    # 2. YEDEK DEPO (EKSİK VARSA TAMAMLA)
    target = 15
    if len(ai_sorulari) < target:
        if "Meslek" in kategori:
            # Sınıf bazlı yedek (Örn: "9. Sınıf Meslek")
            yedek = YEDEK_MESLEK.get(alt_baslik, YEDEK_MESLEK["9. Sınıf Meslek"])
        else:
            # TYT ders bazlı yedek (Örn: "Tarih")
            yedek = YEDEK_TYT.get(alt_baslik, YEDEK_TYT["Genel Deneme"])
            
        # Yedeği karıştır ve ekle
        import copy
        yedek_kopya = copy.deepcopy(yedek)
        random.shuffle(yedek_kopya)
        
        # Eğer yedek yetmezse çoğalt
        while len(yedek_kopya) < (target - len(ai_sorulari)):
            yedek_kopya.extend(yedek_kopya)
            
        ai_sorulari.extend(yedek_kopya[:(target - len(ai_sorulari))])
            
    return ai_sorulari[:target]

# --- KAYIT SİSTEMİ ---
def sonuclari_kaydet(ad, soyad, kategori, alt_baslik, puan):
    try:
        if "gcp_service_account" in st.secrets:
            secrets_dict = st.secrets["gcp_service_account"]
            scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_info(secrets_dict, scopes=scope)
            client = gspread.authorize(creds)
            sheet = client.open("Okul_Puanlari").sheet1
            tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
            sheet.append_row([tarih, f"{ad} {soyad}", kategori, alt_baslik, puan])
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
    # Sidebar
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2997/2997321.png", width=100)
        st.title("Sınav Modu")
        mod_secimi = st.radio("Bir Bölüm Seçin:", ["Meslek Lisesi Sınavları", "TYT Hazırlık Kampı"])
        st.info("Bağarası ÇPAL Yapay Zeka Destekli Sınav Sistemi")

    st.markdown(f"<h1 style='text-align: center; color:#E65100;'>{mod_secimi}</h1>", unsafe_allow_html=True)
    
    if mod_secimi == "Meslek Lisesi Sınavları":
        secenekler = list(MESLEK_GRUPLARI.keys())
        etiket = "Sınıf Seviyesi Seçiniz:"
    else:
        secenekler = ["Türkçe", "Matematik", "Tarih", "Coğrafya", "Genel Deneme"]
        etiket = "Ders / Deneme Seçiniz:"
        
    secilen_alt_baslik = st.selectbox(etiket, secenekler)
    
    if mod_secimi == "Meslek Lisesi Sınavları":
        st.warning(f"📌 **Kapsam:** {', '.join(MESLEK_GRUPLARI[secilen_alt_baslik])}")
    else:
        st.warning("📌 **İçerik:** ÖSYM/TYT Çıkmış Soru Formatı")

    with st.form("giris"):
        c1, c2 = st.columns(2)
        ad = c1.text_input("Adınız")
        soyad = c2.text_input("Soyadınız")
        if st.form_submit_button("SINAVI BAŞLAT 🚀"):
            if ad and soyad:
                st.session_state.kimlik = {"ad": ad, "soyad": soyad, "mod": mod_secimi, "baslik": secilen_alt_baslik}
                st.session_state.yukleniyor = True
                st.rerun()

    if st.session_state.yukleniyor:
        with st.status("Yapay Zeka Soruları Hazırlıyor... (15 Soru)", expanded=True):
            sorular = soru_uret(st.session_state.kimlik['mod'], st.session_state.kimlik['baslik'])
            st.session_state.soru_listesi = sorular
            st.session_state.oturum_basladi = True
            st.session_state.yukleniyor = False
            st.rerun()

# SORU EKRANI
elif st.session_state.index < len(st.session_state.soru_listesi):
    soru = st.session_state.soru_listesi[st.session_state.index]
    toplam = len(st.session_state.soru_listesi)
    st.progress((st.session_state.index + 1) / toplam)
    
    st.markdown(f"**{st.session_state.kimlik['baslik']}** | Soru {st.session_state.index + 1} / {toplam}")
    st.markdown(f"<div class='big-font'>{soru['soru']}</div>", unsafe_allow_html=True)
    
    secenekler = soru["secenekler"]
    random.shuffle(secenekler)
    
    for sec in secenekler:
        if st.button(sec, use_container_width=True):
            if sec == soru["cevap"]:
                st.session_state.puan += (100 / 15)
                st.toast("✅ Doğru!", icon="🎉")
            else:
                st.toast(f"❌ Yanlış! Cevap: {soru['cevap']}", icon="⚠️")
            time.sleep(1)
            st.session_state.index += 1
            st.rerun()

# SONUÇ EKRANI
else:
    st.balloons()
    final_puan = int(st.session_state.puan)
    st.markdown(f"""
    <div style='background-color:#FF7043; padding:30px; border-radius:15px; text-align:center; color:white; box-shadow: 0 10px 20px rgba(0,0,0,0.2);'>
        <h2>{st.session_state.kimlik['ad']} {st.session_state.kimlik['soyad']}</h2>
        <h1 style='font-size: 60px; margin: 10px 0;'>{final_puan}</h1>
        <p style='font-size: 20px;'>{st.session_state.kimlik['baslik']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.kayit_ok:
        if sonuclari_kaydet(st.session_state.kimlik["ad"], st.session_state.kimlik["soyad"], st.session_state.kimlik["mod"], st.session_state.kimlik["baslik"], final_puan):
            st.success("Sonuç Öğretmenine İletildi ✅")
            st.session_state.kayit_ok = True
            
    if st.button("Ana Menüye Dön"):
        st.session_state.oturum_basladi = False
        st.rerun()
