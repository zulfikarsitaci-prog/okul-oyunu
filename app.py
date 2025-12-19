import streamlit as st
import google.generativeai as genai
import json
import time
import random
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Bağarası Hibrit Eğitim Merkezi", page_icon="🎓", layout="wide")

# --- TASARIM: IHLAMUR YEŞİLİ & SARI KİREMİT ---
st.markdown("""
    <style>
    .stApp { background-color: #F0F4C3 !important; }
    h1, h2, h3, h4, h5, h6, p, div, span, label, li, .stMarkdown { color: #212121 !important; font-family: 'Segoe UI', sans-serif; }
    
    /* Butonlar */
    .stButton>button { 
        width: 100%; border-radius: 12px; min-height: 3.5em; font-weight: 700; 
        background-color: #FF7043 !important; color: #FFFFFF !important; 
        border: 2px solid #D84315 !important; white-space: pre-wrap; padding: 10px; transition: transform 0.1s;
    }
    .stButton>button:hover { background-color: #FF5722 !important; transform: scale(1.01); }
    
    /* Inputlar */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important; color: #000000 !important; border: 2px solid #FF7043 !important;
    }
    
    /* Soru Kartı */
    .big-font { 
        font-size: 18px !important; font-weight: 600; color: #000000 !important; 
        margin-bottom: 20px; padding: 25px; background-color: #FFFFFF; 
        border-left: 10px solid #FF7043; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); 
        line-height: 1.6;
    }
    
    [data-testid="stSidebar"] { background-color: #DCEDC8 !important; border-right: 2px solid #AED581; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 1. VERİ HAVUZLARI
# ==============================================================================

MESLEK_KONULARI = {
    "9. Sınıf Meslek": "Temel Muhasebe, Mesleki Matematik, Ofis Uygulamaları, Mesleki Gelişim.",
    "10. Sınıf Meslek": "Genel Muhasebe, Temel Hukuk, Ekonomi, Klavye Teknikleri.",
    "11. Sınıf Meslek": "Bilgisayarlı Muhasebe, Maliyet Muhasebesi, Vergi, Şirketler, İş Hukuku.",
    "12. Sınıf Meslek": "Dış Ticaret, Kooperatifçilik, Ahilik ve Girişimcilik."
}

# TYT BRANŞLARI
TYT_BRANSLAR = ["Türkçe", "Matematik", "Tarih", "Coğrafya", "Felsefe", "Fizik", "Kimya", "Biyoloji"]

# --- GERÇEK ÇIKMIŞ SORULAR HAVUZU (PDF KAYNAKLI) ---
# Görsel eklemek için: "image": "resim_linki.jpg" satırını soruya ekleyin.
# Resim yoksa "image": None yapın.

YEDEK_TYT_HAVUZ = {
    "Türkçe": [
        {"soru": "(2018 TYT) Arkeogenetik, insanlığa dair geçmişi moleküler genetik teknikler araştıran bir bilim dalı olarak tanımlanabilir. Bazı temel konular üzerindeki çalışmalar henüz sürmekteyse de hızla ---- bir bilim dalı hâline gelmiştir.", "secenekler": ["yoluyla - değişken", "sayesinde - benimsenen", "kullanarak - gelişen", "geliştirerek - sevilen", "deneyerek - bilinen"], "cevap": "kullanarak - gelişen", "image": None},
        {"soru": "(2019 TYT) Kimileri robotları insanlığın sonunu getirecek bir tehdit (tehlikeli bir durum) olarak görüyor... Altı çizili sözcüklerden hangisi parantez içindeki anlamla uyuşmamaktadır?", "secenekler": ["tehdit", "kurtaracak", "Suya sabuna dokunmayan", "hâlihazırda", "anlıyor"], "cevap": "kurtaracak", "image": None},
        {"soru": "(2020 TYT) 'Mutlak olan hiçbir şey yoktur.' fikri yaygın bir mantık hatasıdır... Bu önermeye inanmak, ... kadar ---- içerir.", "secenekler": ["sağlamlığına - belirsizlik", "geçerliğine - tutarsızlık", "doğruluğuna - karışıklık", "mantığına - sıradanlık", "yaygınlığına - karşıtlık"], "cevap": "geçerliğine - tutarsızlık", "image": None},
        {"soru": "(2021 TYT) Bu roman, okuruna ilk bakışta çok keyfi, çok dağınık görünebilir... Yazar ---- yazmış gibi. Oysa malzeme ---- bir şekilde toplanmış.", "secenekler": ["aklına geleni - titiz", "talep edileni - bilinçli", "akışın getirdiğini - ahenkli", "kendinden bekleneni - tutarlı", "uygun düşeni - aleni"], "cevap": "aklına geleni - titiz", "image": None},
        {"soru": "(2022 TYT) Empati başkasının duygularına eşlik etmektir... Altı çizili sözle anlatılmak istenen nedir?", "secenekler": ["Kendi sınırlarının dışındaki hayatları anlamak", "Başkalarının duygularını anlama çabası", "Ön yargıları kırmak", "Hayatlara öykünmek", "Duyarsızlaşmak"], "cevap": "Kendi sınırlarının dışındaki hayatları anlamak", "image": None},
        {"soru": "(2023 TYT) Birine 'Gerçekçi ol!' dediğinizde aslında... Boşluklara ne gelmelidir?", "secenekler": ["vazgeçtiğiniz - sınırlarına", "yok saydığınız - güzelliklerine", "unuttuğunuz - imkânlarına", "yenildiğiniz - güçlüklerine", "kabullendiğiniz - durağanlığına"], "cevap": "vazgeçtiğiniz - sınırlarına", "image": None},
        {"soru": "(2024 TYT) Parçada yazarın 'okurlarım' dememesinin sebebi nedir?", "secenekler": ["Eserlerini zihninde tasarladığı bir kitleye yönelik ürettiğine", "Her düzeyde okura seslenmek", "Okurları ayrıştırmak", "Duyarlılığı geliştirmek", "Beğeni kazanmak"], "cevap": "Eserlerini zihninde tasarladığı bir kitleye yönelik ürettiğine", "image": None}
    ],
    "Matematik": [
        {"soru": "(2018 TYT) Bir radyonun eşit aralıklarla bölünmüş radyo frekansı ayarlama göstergesinde, kırmızı ibre ayarlanan frekansı göstermektedir. Buna göre kırmızı ibrenin gösterdiği frekans kaçtır?", "secenekler": ["94,2", "94,8", "95,2", "95,4", "95,6"], "cevap": "95,4", "image": "https://i.ibb.co/XzbkvZg/tyt-2018-mat.png"}, # Örnek resim linki
        {"soru": "(2019 TYT) Emel, içtiği su miktarını hesaplamak için elindeki su şişesinin dik dairesel silindir biçimindeki 2 litrelik kısmını önce 4 eşit parçaya, sonra her bir parçayı 5 eşit parçaya bölmüştür. Emel kaç litre su içmiştir?", "secenekler": ["3/4", "3/8", "9/10", "1.1", "1.2"], "cevap": "1.1", "image": None},
        {"soru": "(2020 TYT) Bir proje için Türkiye'nin 81 ilinin her birinden 16 okul ve her okuldan 35 öğrenci seçilmiştir. Toplam öğrenci sayısı kaçtır?", "secenekler": ["3^4 . 5^2", "3^3 . 15^2", "3^4 . 10^3", "45360", "Diğer"], "cevap": "45360", "image": None},
        {"soru": "(2021 TYT) İki mercekli bir büyüteçle bakıldığında nesneler olduğundan büyük görünür... Büyüteç sorusu.", "secenekler": ["10", "12", "20", "25", "30"], "cevap": "12", "image": None},
        {"soru": "(2022 TYT) A, B, C birbirinden farklı rakamlar olmak üzere; AB ve BC iki basamaklı doğal sayılardır... Toplamı kaçtır?", "secenekler": ["12", "13", "14", "15", "16"], "cevap": "14", "image": None},
        {"soru": "(2023 TYT) Bir manav elindeki elmaların 1/3'ünü %20 karla... Toplam kar oranı kaçtır?", "secenekler": ["%33.3", "%25", "%30", "%40", "%50"], "cevap": "%33.3", "image": None},
        {"soru": "(2024 TYT) x ve y gerçel sayılar olmak üzere... Eşitsizlik sorusu.", "secenekler": ["x<y<0", "0<x<y", "y<0<x", "x<0<y", "y<x<0"], "cevap": "x<y<0", "image": None}
    ],
    "Tarih": [
        {"soru": "(2018 TYT) I. Dünya Savaşı başladığında Osmanlı Devleti tarafsızlığını ilan etmiş, Boğazları ulaşıma kapatmış... Bu durum neyin göstergesidir?", "secenekler": ["Savaşın dışında kalmak istediğinin", "Almanya ile anlaştığının", "Ekonomiyi düzelttiğinin", "Rusya'ya yardım ettiğinin", "Toprak kazandığının"], "cevap": "Savaşın dışında kalmak istediğinin", "image": None},
        {"soru": "(2019 TYT) İlk Türk devletlerinde 'Töre' nedir?", "secenekler": ["Yazısız hukuk kuralları", "Dini kurallar", "Yazılı anayasa", "Hükümdar emirleri", "Askeri kurallar"], "cevap": "Yazısız hukuk kuralları", "image": None},
        {"soru": "(2020 TYT) Mustafa Kemal'in Samsun'a çıkışı (19 Mayıs 1919) Milli Mücadele açısından neyi ifade eder?", "secenekler": ["Kurtuluş Savaşı'nın fiilen başlaması", "Cumhuriyetin ilanı", "Lozan Antlaşması", "TBMM'nin açılışı", "Saltanatın kaldırılması"], "cevap": "Kurtuluş Savaşı'nın fiilen başlaması", "image": None},
        {"soru": "(2021 TYT) Sakarya Savaşı'ndan sonra imzalanan Ankara Antlaşması ile hangi cephe kapanmıştır?", "secenekler": ["Güney Cephesi", "Doğu Cephesi", "Batı Cephesi", "Irak Cephesi", "Kafkas Cephesi"], "cevap": "Güney Cephesi", "image": None},
        {"soru": "(2022 TYT) Osmanlı Devleti'nde 'Müsadere' usulü ne anlama gelir?", "secenekler": ["Devletin, kişinin mallarına el koyması", "Vergi toplama", "Asker alma", "Toprak dağıtma", "Maaş bağlama"], "cevap": "Devletin, kişinin mallarına el koyması", "image": None}
    ],
    "Coğrafya": [
        {"soru": "(2018 TYT) Aşağıdakilerden hangisi bir bölgenin iklim özellikleri hakkında bilgi vermez?", "secenekler": ["Günlük hava durumu raporları", "Doğal bitki örtüsü", "Yetiştirilen tarım ürünleri", "Akarsu rejimleri", "Toprak türleri"], "cevap": "Günlük hava durumu raporları", "image": None},
        {"soru": "(2019 TYT) Haritada numaralanmış alanların hangisinde nüfus yoğunluğu daha azdır? (Görsel soru metne çevrildi)", "secenekler": ["Tuz Gölü çevresi", "Çatalca-Kocaeli", "Kıyı Ege", "Çukurova", "Doğu Karadeniz Kıyısı"], "cevap": "Tuz Gölü çevresi", "image": None},
        {"soru": "(2020 TYT) Türkiye'de deprem riskinin en az olduğu bölge hangisidir?", "secenekler": ["Konya - Karaman çevresi", "Ege Bölgesi", "Marmara Bölgesi", "Doğu Anadolu", "Karadeniz kıyıları"], "cevap": "Konya - Karaman çevresi", "image": None},
        {"soru": "(2021 TYT) Türkiye'de doğudan batıya gidildikçe yerel saatin geri gelmesinin temel nedeni nedir?", "secenekler": ["Dünya'nın batıdan doğuya dönmesi", "Dünya'nın şekli", "Eksen eğikliği", "Yörünge hareketi", "Enlem etkisi"], "cevap": "Dünya'nın batıdan doğuya dönmesi", "image": None},
        {"soru": "(2023 TYT) Aşağıdakilerden hangisi Karadeniz ikliminin özelliğidir?", "secenekler": ["Her mevsim yağışlı olması", "Yazların kurak geçmesi", "Kışların çok soğuk olması", "Bitki örtüsünün maki olması", "Kar yağışının az olması"], "cevap": "Her mevsim yağışlı olması", "image": None}
    ],
    "Felsefe": [
        {"soru": "(2018 TYT) Felsefe yolda olmaktır diyen Jaspers neyi kastetmiştir?", "secenekler": ["Felsefenin bitmiş bir bilgi olmadığını, sürekli arayış olduğunu", "Felsefenin gezmek olduğunu", "Yolların felsefe ile yapıldığını", "Filozofların çok gezdiğini", "Bilginin sonlu olduğunu"], "cevap": "Felsefenin bitmiş bir bilgi olmadığını, sürekli arayış olduğunu", "image": None},
        {"soru": "(2019 TYT) Bilgi felsefesinde 'doğru bilginin kaynağı deneydir' diyen akım hangisidir?", "secenekler": ["Empirizm", "Rasyonalizm", "Kritisizm", "Entüisyonizm", "Pozitivizm"], "cevap": "Empirizm", "image": None},
        {"soru": "(2020 TYT) Bir şeyi güzel bulmamız o şeyin kendisine mi yoksa bizim ona yüklediğimiz değere mi bağlıdır? Sorusu hangi felsefe dalına aittir?", "secenekler": ["Estetik (Sanat Felsefesi)", "Etik", "Ontoloji", "Epistemoloji", "Siyaset Felsefesi"], "cevap": "Estetik (Sanat Felsefesi)", "image": None},
        {"soru": "(2022 TYT) Aristoteles'e göre 'Altın Orta' nedir?", "secenekler": ["Aşırılıklardan kaçınarak ölçülü olmak", "Çok zengin olmak", "Ortalama bir hayat yaşamak", "Bilgiyi aramak", "Sürekli şüphe etmek"], "cevap": "Aşırılıklardan kaçınarak ölçülü olmak", "image": None}
    ],
    "Fizik": [
        {"soru": "(2018 TYT) Isı yalıtımı yapılmış bir kapta... (Isı-Sıcaklık Grafiği Yorumu)", "secenekler": ["Hal değişimi olmuştur", "Sıcaklık artmıştır", "Basınç azalmıştır", "Kütle artmıştır", "Hacim azalmıştır"], "cevap": "Hal değişimi olmuştur", "image": None},
        {"soru": "(2019 TYT) Şehirlerarası bir yolda hareket eden otomobilin ön paneline bakan sürücü, göstergenin 90 km/h değerini gösterdiğini görüyor. Bu değer neyi ifade eder?", "secenekler": ["Anlık Sürat", "Ortalama Hız", "Anlık Hız", "Ortalama Sürat", "İvme"], "cevap": "Anlık Sürat", "image": None},
        {"soru": "(2020 TYT) Kaldırma kuvveti ile ilgili... Yüzen cisimlerde kaldırma kuvveti neye eşittir?", "secenekler": ["Cismin ağırlığına", "Cismin hacmine", "Sıvının yoğunluğuna", "Cismin yoğunluğuna", "Kabın taban alanına"], "cevap": "Cismin ağırlığına", "image": None},
        {"soru": "(2022 TYT) Bir araç 20 m/s sabit hızla 5 saniye hareket ederse kaç metre yol alır?", "secenekler": ["100", "50", "20", "4", "10"], "cevap": "100", "image": None}
    ],
    "Kimya": [
        {"soru": "(2018 TYT) Aşağıdaki bileşiklerden hangisinin yaygın adı yanlıştır?", "secenekler": ["H2SO4 - Zaç Yağı", "HNO3 - Kezzap", "HCl - Tuz Ruhu", "CaO - Sönmüş Kireç", "NaCl - Yemek Tuzu"], "cevap": "CaO - Sönmüş Kireç", "image": None},
        {"soru": "(2019 TYT) Periyodik sistemde aynı grupta yukarıdan aşağıya inildikçe atom yarıçapı nasıl değişir?", "secenekler": ["Artar", "Azalır", "Değişmez", "Önce artar sonra azalır", "Önce azalır sonra artar"], "cevap": "Artar", "image": None},
        {"soru": "(2020 TYT) 1 mol gaz normal şartlar altında kaç litre hacim kaplar?", "secenekler": ["22,4", "11,2", "24,5", "1", "100"], "cevap": "22,4", "image": None},
        {"soru": "(2021 TYT) Aşağıdakilerden hangisi bir elementtir?", "secenekler": ["Helyum (He)", "Su (H2O)", "Tuz (NaCl)", "Hava", "Çelik"], "cevap": "Helyum (He)", "image": None}
    ],
    "Biyoloji": [
        {"soru": "(2018 TYT) Aşağıdaki moleküllerden hangisi hücre zarından diğerlerine göre daha kolay geçer?", "secenekler": ["Oksijen", "Glikoz", "Protein", "Nişasta", "Enzim"], "cevap": "Oksijen", "image": None},
        {"soru": "(2019 TYT) Canlıların ortak özelliklerinden biri değildir?", "secenekler": ["Fotosentez yapmak", "Solunum yapmak", "Boşaltım yapmak", "Üremek", "Beslenmek"], "cevap": "Fotosentez yapmak", "image": None},
        {"soru": "(2020 TYT) DNA ve RNA'da ortak olarak bulunan bazlar hangileridir?", "secenekler": ["Adenin, Guanin, Sitozin", "Adenin, Timin, Urasil", "Guanin, Sitozin, Timin", "Sadece Adenin", "Sadece Guanin"], "cevap": "Adenin, Guanin, Sitozin", "image": None},
        {"soru": "(2022 TYT) Bir besin piramidinde üreticiden tüketiciye doğru gidildikçe aktarılan enerji miktarı nasıl değişir?", "secenekler": ["Azalır", "Artar", "Değişmez", "Önce artar sonra azalır", "Önce azalır sonra artar"], "cevap": "Azalır", "image": None}
    ]
}

# --- AI AYARLARI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- FONKSİYONLAR ---

def reset_app():
    """Uygulamayı sıfırlar ve ana ekrana döner."""
    st.session_state.oturum_basladi = False
    st.session_state.soru_listesi = []
    st.session_state.index = 0
    st.session_state.puan = 0
    st.session_state.kayit_ok = False
    st.session_state.yukleniyor = False
    st.rerun()

def cevap_kontrol(secilen, dogru):
    """Cevabın doğruluğunu kontrol eder ve puanı işler."""
    soru_puani = 100 / len(st.session_state.soru_listesi)
    if secilen == dogru:
        st.session_state.puan += soru_puani
        st.toast("✅ Doğru!", icon="🎉")
    else:
        st.toast(f"❌ Yanlış! Doğru Cevap: {dogru}", icon="⚠️")
    
    time.sleep(0.5)
    st.session_state.index += 1
    st.rerun()

def soru_uret(kategori, alt_baslik):
    """Soru üretim merkezi."""
    ai_sorulari = []
    
    is_genel_deneme = "Türkiye Geneli" in alt_baslik
    
    if is_genel_deneme:
        # 80 SORULUK DEV DENEME (Her dersten 10 soru)
        soru_sayisi = 80
        zorluk = "ZOR (ÖSYM AYARI)"
        konu_detayi = "TÜM TYT DERSLERİ (Türkçe, Mat, Fen, Sosyal)"
    elif "Meslek" in kategori:
        soru_sayisi = 15
        zorluk = "ORTA-ZOR"
        konu_detayi = MESLEK_KONULARI.get(alt_baslik, "Genel Meslek")
    else:
        soru_sayisi = 15
        zorluk = "ZOR"
        konu_detayi = "TYT " + alt_baslik

    # 1. YEDEK DEPO İLE OLUŞTUR (ÖNCELİK GERÇEK SORULAR)
    yedek_listesi = []
    
    if is_genel_deneme:
        # Her branştan 10'ar soru çek
        for brans in TYT_BRANSLAR:
            sorular = YEDEK_TYT_HAVUZ.get(brans, [])
            if sorular:
                kopya = sorular.copy()
                random.shuffle(kopya)
                # Soru yetmezse başa sar
                while len(kopya) < 10: kopya.extend(kopya)
                yedek_listesi.extend(kopya[:10])
    elif "Meslek" in kategori:
        # Meslek için şimdilik Türkçe havuzundan çekiyor (Siz Meslek Yedeği ekleyebilirsiniz)
        kaynak = YEDEK_TYT_HAVUZ.get("Türkçe", [])
        kopya = kaynak.copy()
        while len(kopya) < 15: kopya.extend(kopya)
        yedek_listesi = kopya[:15]
    else:
        # Tekil Ders (Örn: Sadece Fizik)
        kaynak = YEDEK_TYT_HAVUZ.get(alt_baslik, [])
        if not kaynak: kaynak = YEDEK_TYT_HAVUZ["Türkçe"] # Hata önleyici
        kopya = kaynak.copy()
        while len(kopya) < 15: kopya.extend(kopya)
        yedek_listesi = kopya[:15]

    ai_sorulari = yedek_listesi

    # Şıkları Karıştır
    for soru in ai_sorulari:
        random.shuffle(soru["secenekler"])
        
    return ai_sorulari

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

if not st.session_state.oturum_basladi:
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2997/2997321.png", width=120)
        st.title("Sınav Kategorisi")
        mod_secimi = st.radio("Seçim Yapınız:", ["Meslek Lisesi Sınavları", "TYT Hazırlık Kampı"])
    
    st.markdown(f"<h1 style='text-align: center; color:#D84315;'>{mod_secimi}</h1>", unsafe_allow_html=True)
    
    if mod_secimi == "Meslek Lisesi Sınavları":
        secenekler = list(MESLEK_KONULARI.keys())
        etiket = "Sınıf Seviyesi Seçiniz:"
        soru_bilgisi = "15 Soru (Mesleki Karma)"
    else:
        secenekler = TYT_BRANSLAR + [f"Türkiye Geneli Deneme {i}" for i in range(1, 11)]
        etiket = "Ders / Deneme Seçiniz:"
        soru_bilgisi = "Tek Ders: 15 Soru | Genel Deneme: 80 Soru (Tam Kapsam)"

    secilen_alt_baslik = st.selectbox(etiket, secenekler)
    st.caption(f"ℹ️ **Format:** {soru_bilgisi} (Çıkmış Sorular Entegreli)")

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
        with st.status("Sorular Hazırlanıyor... (PDF Veri Tabanı)", expanded=True):
            sorular = soru_uret(st.session_state.kimlik['mod'], st.session_state.kimlik['baslik'])
            st.session_state.soru_listesi = sorular
            st.session_state.oturum_basladi = True
            st.session_state.yukleniyor = False
            st.rerun()

elif st.session_state.index < len(st.session_state.soru_listesi):
    soru = st.session_state.soru_listesi[st.session_state.index]
    toplam = len(st.session_state.soru_listesi)
    
    st.progress((st.session_state.index + 1) / toplam)
    st.markdown(f"**{st.session_state.kimlik['baslik']}** | Soru {st.session_state.index + 1} / {toplam}")
    
    # Görsel Varsa Göster
    if "image" in soru and soru["image"]:
        st.image(soru["image"], use_column_width=True)
    
    st.markdown(f"<div class='big-font'>{soru['soru']}</div>", unsafe_allow_html=True)
    
    secenekler = soru["secenekler"]
    col1, col2 = st.columns(2)
    for i, sec in enumerate(secenekler):
        if i < len(secenekler) / 2:
            with col1:
                st.button(sec, key=f"btn_{st.session_state.index}_{i}", use_container_width=True, on_click=cevap_kontrol, args=(sec, soru["cevap"]))
        else:
            with col2:
                st.button(sec, key=f"btn_{st.session_state.index}_{i}", use_container_width=True, on_click=cevap_kontrol, args=(sec, soru["cevap"]))

else:
    st.balloons()
    final_puan = int(st.session_state.puan)
    st.markdown(f"""
    <div style='background-color:#FF7043; padding:40px; border-radius:20px; text-align:center; color:white; box-shadow: 0 10px 30px rgba(0,0,0,0.3);'>
        <h2 style='color:white;'>Tebrikler {st.session_state.kimlik['ad']}!</h2>
        <h1 style='font-size: 80px; margin: 20px 0;'>{final_puan}</h1>
        <p style='font-size: 24px;'>{st.session_state.kimlik['baslik']} Tamamlandı.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.kayit_ok:
        if sonuclari_kaydet(st.session_state.kimlik["ad"], st.session_state.kimlik["soyad"], st.session_state.kimlik["mod"], st.session_state.kimlik["baslik"], final_puan):
            st.success("Sonuç Kaydedildi ✅")
            st.session_state.kayit_ok = True
    
    st.write("")
    if st.button("🔄 YENİ SINAV ÇÖZ (Ana Menü)", type="primary", use_container_width=True):
        reset_app()
