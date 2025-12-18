import streamlit as st
import google.generativeai as genai
import json
import time
import random
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Bağarası ÇPAL Sınav Merkezi", page_icon="🧮", layout="centered")

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
    .big-font { font-size: 20px !important; font-weight: 800; color: #000000 !important; margin-bottom: 25px; padding: 15px; border-left: 6px solid #F57F17; background: rgba(255,255,255,0.6); }
    </style>
""", unsafe_allow_html=True)

# --- 1. MÜFREDAT LİSTESİ ---
MUFREDAT = {
    "9. Sınıf": ["Temel Muhasebe", "Mesleki Matematik", "Ofis Uygulamaları", "Mesleki Gelişim Atölyesi"],
    "10. Sınıf": ["Genel Muhasebe", "Temel Hukuk", "Ekonomi", "Klavye Teknikleri"],
    "11. Sınıf": ["Bilgisayarlı Muhasebe", "Maliyet Muhasebesi", "Şirketler Muhasebesi", "Vergi ve Beyannameler", "İş ve Sosyal Güvenlik Hukuku", "Girişimcilik"],
    "12. Sınıf": ["Dış Ticaret", "Kooperatifçilik", "Hızlı Klavye", "Ahilik Kültürü"]
}

# --- 2. KONU HAVUZU (DOSYALARDAN ÇEKİLEN GERÇEK MÜFREDAT) ---
KONU_HAVUZU = {
    "9-Temel Muhasebe": "Ticari Defterler, Fatura, İrsaliye, Perakende Satış Fişi, Gider Pusulası, Müstahsil Makbuzu, Serbest Meslek Makbuzu, İşletme Hesabı Defteri (Gider/Gelir), Vergi Dairesi, Belediye, SGK İşlemleri.",
    "9-Mesleki Matematik": "Dört İşlem Pratikleri, Yüzde Hesapları, Binde Hesapları, Maliyet Fiyatı, Satış Fiyatı, Kar ve Zarar Hesapları, KDV Hesaplamaları (Dahil/Hariç), Oran ve Orantı.",
    "9-Ofis Uygulamaları": "Word Biçimlendirme, Excel Formülleri (Topla, Ortalama, Eğer), PowerPoint Tasarımı, Donanım Birimleri.",
    "9-Mesleki Gelişim Atölyesi": "Ahilik Kültürü, Meslek Etiği, İletişim Türleri, İş Sağlığı ve Güvenliği, Proje Hazırlama.",
    
    "10-Genel Muhasebe": "Bilanço Eşitliği, Hesap Kavramı, Tek Düzen Hesap Planı, Dönen/Duran Varlıklar, Yabancı Kaynaklar, Yevmiye Defteri, Büyük Defter, Mizan, Gelir Tablosu İlkeleri.",
    "10-Temel Hukuk": "Hukukun Kaynakları, Hak Ehliyeti, Kişiler Hukuku, Borçlar Hukuku (Sözleşmeler), Ticaret Hukuku (Tacir), Kıymetli Evrak (Çek, Senet), Sigorta Hukuku.",
    "10-Ekonomi": "Arz-Talep, Piyasa Dengesi, Enflasyon, Devalüasyon, Milli Gelir, Para ve Bankacılık, Merkez Bankası, Dış Ticaret Dengesi.",
    "10-Klavye Teknikleri": "F Klavye Tuşları, Oturuş Düzeni, Süreli Yazım, Hatasız Yazım Kuralları, Rakam Tuşları.",
    
    "11-Bilgisayarlı Muhasebe": "ETA/Luca Şirket Açma, Stok/Cari Kart, Fatura İşleme, Muhasebe Fişleri (Tahsil/Tediye), Çek/Senet, KDV Beyannamesi.",
    "11-Maliyet Muhasebesi": "7A ve 7B Hesapları, Direkt İlk Madde (150), Direkt İşçilik (720), Genel Üretim (730), Satılan Mamul Maliyeti, Hizmet Maliyeti.",
    "11-Şirketler Muhasebesi": "Şirket Kuruluşu (Kolektif, A.Ş., Ltd.), Sermaye Artırımı, Kar Dağıtımı, Tasfiye, Birleşme.",
    "11-Vergi ve Beyannameler": "Vergi Usul Kanunu, Gelir Vergisi, Kurumlar Vergisi, KDV, ÖTV, MTV, Muhtasar Beyanname, Geçici Vergi Beyannamesi.",
    "11-İş ve Sosyal Güvenlik Hukuku": "İş Kanunu, İş Sözleşmesi, Kıdem Tazminatı, İhbar Tazminatı, Ücret Bordrosu, SGK 4a/4b/4c.",
    "11-Girişimcilik": "Girişimcilik Türleri, İş Planı, Fizibilite, Pazar Araştırması, KOSGEB Destekleri, İnovasyon.",
    
    "12-Dış Ticaret": "İhracat/İthalat Rejimi, Teslim Şekilleri (Incoterms), Ödeme Şekilleri, Gümrük Mevzuatı, Kambiyo, Serbest Bölgeler.",
    "12-Kooperatifçilik": "Kooperatif İlkeleri, Kuruluş, Ana Sözleşme, Ortaklık Hakları, Genel Kurul, Risturn.",
    "12-Hızlı Klavye": "İleri Seviye Yazım, Adli/Hukuki Metinler, Zabıt Kâtipliği Metinleri.",
    "12-Ahilik Kültürü": "Ahilik Teşkilatı, Fütüvvetname, Usta-Çırak İlişkisi, Meslek Ahlakı, E-Ticaret."
}

# --- 3. GENİŞLETİLMİŞ YEDEK SORU DEPOSU (MATEMATİK İÇİN ÖZEL HAVUZ) ---
# Burası "Genel" havuza düşmesin diye her dersin adıyla birebir eşleştirildi.
YEDEK_DEPO = {
    # --- 9. SINIF MATEMATİK (20 SORU) ---
    "9-Mesleki Matematik": [
        {"soru": "KDV hariç 500 TL olan bir malın %20 KDV tutarı kaç TL'dir?", "secenekler": ["100 TL", "50 TL", "20 TL", "120 TL", "80 TL"], "cevap": "100 TL"},
        {"soru": "Maliyeti 200 TL olan bir gömlek %50 karla kaç TL'ye satılır?", "secenekler": ["300 TL", "250 TL", "400 TL", "350 TL", "220 TL"], "cevap": "300 TL"},
        {"soru": "Yarısının 3 fazlası 13 olan sayı kaçtır?", "secenekler": ["20", "10", "15", "25", "18"], "cevap": "20"},
        {"soru": "Bir işçi günde 8 saat çalışarak bir işi 5 günde bitiriyor. Aynı işi günde 10 saat çalışarak kaç günde bitirir?", "secenekler": ["4 Gün", "3 Gün", "6 Gün", "2 Gün", "5 Gün"], "cevap": "4 Gün"},
        {"soru": "1000 TL'nin %18 KDV dahil fiyatı yaklaşık ne kadardır?", "secenekler": ["1180 TL", "1018 TL", "1200 TL", "1100 TL", "1080 TL"], "cevap": "1180 TL"},
        {"soru": "Etiket fiyatı 400 TL olan bir ürüne %25 indirim yapılırsa yeni fiyat ne olur?", "secenekler": ["300 TL", "350 TL", "250 TL", "100 TL", "375 TL"], "cevap": "300 TL"},
        {"soru": "Bir kırtasiyeci 50 kuruşa aldığı kalemi 1 TL'ye satarsa kar oranı yüzde kaçtır?", "secenekler": ["%100", "%50", "%25", "%10", "%200"], "cevap": "%100"},
        {"soru": "Basit faiz formülünde (A.n.t/100) 'n' neyi ifade eder?", "secenekler": ["Faiz Oranını", "Anaparayı", "Zamanı", "Vergiyi", "Kar Payını"], "cevap": "Faiz Oranını"},
        {"soru": "Aşağıdaki oranlardan hangisi 'Yarım'ı ifade eder?", "secenekler": ["%50", "%25", "%10", "%100", "%75"], "cevap": "%50"},
        {"soru": "Bir malın alış fiyatı üzerine yapılan giderler eklenince ne bulunur?", "secenekler": ["Maliyet Fiyatı", "Satış Fiyatı", "Kar", "Ciro", "Zarar"], "cevap": "Maliyet Fiyatı"},
        {"soru": "1200 TL'nin %10'u kaç TL eder?", "secenekler": ["120 TL", "12 TL", "100 TL", "150 TL", "10 TL"], "cevap": "120 TL"},
        {"soru": "Hangi sayı 4'e tam bölünür?", "secenekler": ["100", "22", "33", "45", "50"], "cevap": "100"},
        {"soru": "Karışım problemlerinde saf madde oranı nasıl bulunur?", "secenekler": ["Saf Madde / Toplam Karışım", "Su / Şeker", "Toplam / Saf Madde", "Alış / Satış", "Kar / Zarar"], "cevap": "Saf Madde / Toplam Karışım"},
        {"soru": "80 TL'ye alınan bir ürün 60 TL'ye satılırsa zarar yüzde kaçtır?", "secenekler": ["%25", "%20", "%30", "%10", "%50"], "cevap": "%25"},
        {"soru": "KDV hariç tutardan KDV dahil tutarı bulmak için tutar kaçla çarpılır? (%20 KDV için)", "secenekler": ["1.20", "0.20", "1.18", "0.18", "2.0"], "cevap": "1.20"}
    ],
    # --- 10. SINIF EKONOMİ YEDEKLERİ ---
    "10-Ekonomi": [
        {"soru": "İnsan ihtiyaçlarını karşılayan mal ve hizmetlerin az olmasına ne denir?", "secenekler": ["Kıtlık", "Bolluk", "Enflasyon", "Fayda", "Tüketim"], "cevap": "Kıtlık"},
        {"soru": "Bir malın fiyatı artarsa talebi ne olur?", "secenekler": ["Azalır", "Artar", "Değişmez", "Sıfırlanır", "Çoğalır"], "cevap": "Azalır"},
        {"soru": "Fiyatlar genel düzeyinin sürekli artmasına ne denir?", "secenekler": ["Enflasyon", "Devalüasyon", "Resesyon", "Deflasyon", "Kriz"], "cevap": "Enflasyon"},
        {"soru": "Üretim faktörleri nelerdir?", "secenekler": ["Emek, Sermaye, Doğal Kaynak, Girişimci", "Para, Banka, Çek, Senet", "Alıcı, Satıcı, Devlet, Vergi", "Mal, Hizmet, Fayda, Zarar", "İnsan, Makine, Bina, Arsa"], "cevap": "Emek, Sermaye, Doğal Kaynak, Girişimci"},
        {"soru": "Hangisi bir 'Tam Rekabet Piyasası' özelliğidir?", "secenekler": ["Çok sayıda alıcı ve satıcı vardır", "Tek satıcı vardır", "Fiyatı devlet belirler", "Rekabet yasaktır", "Mal çeşitliliği azdır"], "cevap": "Çok sayıda alıcı ve satıcı vardır"},
        {"soru": "GSYİH (Gayri Safi Yurtiçi Hasıla) neyi ölçer?", "secenekler": ["Bir ülkedeki toplam üretimi", "Toplam borcu", "Döviz kurunu", "İşsizlik oranını", "Vergi gelirini"], "cevap": "Bir ülkedeki toplam üretimi"}
    ],
    # --- 11. SINIF VERGİ YEDEKLERİ ---
    "11-Vergi ve Beyannameler": [
        {"soru": "KDV beyannamesi hangi sıklıkla verilir?", "secenekler": ["Aylık", "Yıllık", "Haftalık", "Günlük", "6 Aylık"], "cevap": "Aylık"},
        {"soru": "Motorlu Taşıtlar Vergisi (MTV) ne zaman ödenir?", "secenekler": ["Ocak ve Temmuz aylarında", "Her ay", "Yıl sonunda", "Mart ve Eylül", "Satış anında"], "cevap": "Ocak ve Temmuz aylarında"},
        {"soru": "Gelir vergisinin konusu nedir?", "secenekler": ["Gerçek kişilerin kazançları", "Şirket kazançları", "Harcamalar", "Emlak", "Miras"], "cevap": "Gerçek kişilerin kazançları"},
        {"soru": "Hangisi dolaylı bir vergidir?", "secenekler": ["KDV", "Gelir Vergisi", "Kurumlar Vergisi", "Emlak Vergisi", "MTV"], "cevap": "KDV"},
        {"soru": "Vergi Usul Kanunu'na göre defter saklama süresi kaç yıldır?", "secenekler": ["5 Yıl", "10 Yıl", "3 Yıl", "1 Yıl", "20 Yıl"], "cevap": "5 Yıl"}
    ],
    # --- 9. SINIF TEMEL MUHASEBE YEDEKLERİ ---
    "9-Temel Muhasebe": [
        {"soru": "Çiftçiden ürün alırken hangi belge düzenlenir?", "secenekler": ["Müstahsil Makbuzu", "Fatura", "Gider Pusulası", "İrsaliye", "Fiş"], "cevap": "Müstahsil Makbuzu"},
        {"soru": "Malın sevkiyatı sırasında araçta bulunması zorunlu belge nedir?", "secenekler": ["Sevk İrsaliyesi", "Fatura", "Gider Pusulası", "Tahsilat Makbuzu", "Dekont"], "cevap": "Sevk İrsaliyesi"},
        {"soru": "Serbest meslek erbabının (Avukat, Doktor) düzenlediği makbuz hangisidir?", "secenekler": ["Serbest Meslek Makbuzu", "Fatura", "Fiş", "Gider Pusulası", "Poliçe"], "cevap": "Serbest Meslek Makbuzu"},
        {"soru": "İşletme defterinin sol tarafına ne yazılır?", "secenekler": ["Giderler", "Gelirler", "Karlar", "Satışlar", "Alacaklar"], "cevap": "Giderler"},
        {"soru": "Vergi levhası nereden alınır?", "secenekler": ["GİB İnternet Vergi Dairesi", "Belediye", "Muhtarlık", "Noter", "Valilik"], "cevap": "GİB İnternet Vergi Dairesi"}
    ],
    # --- GENEL YEDEK (SADECE ACİL DURUM İÇİN) ---
    "Genel": [
        {"soru": "Türkiye'nin para birimi nedir?", "secenekler": ["Türk Lirası", "Dolar", "Euro", "Sterlin", "Yen"], "cevap": "Türk Lirası"},
        {"soru": "Başkentimiz neresidir?", "secenekler": ["Ankara", "İstanbul", "İzmir", "Antalya", "Bursa"], "cevap": "Ankara"},
        {"soru": "Bir hafta kaç gündür?", "secenekler": ["7", "5", "10", "12", "30"], "cevap": "7"}
    ]
}

# --- AI AYARLARI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def yapay_zeka_soru_uret(sinif, ders):
    ai_sorulari = []
    
    # Sınıf numarasını al (örn: "9. Sınıf" -> "9")
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
    # Eğer AI eksik verdiyse veya çalışmadıysa yedekten çek
    if len(ai_sorulari) < 10:
        # 1. Tam eşleşen yedeği bul
        ozel_yedek = YEDEK_DEPO.get(ders_key, [])
        
        # 2. Bulamazsa sadece ders adına bak (Örn: "Maliyet Muhasebesi" anahtar kelimesi geçiyor mu?)
        if not ozel_yedek:
            for key, val in YEDEK_DEPO.items():
                if ders in key or key in ders:
                    ozel_yedek = val
                    break
        
        # 3. Hala yoksa "Genel" yedekten çek (Son Çare)
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
