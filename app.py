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

# --- GÖRÜNTÜ AYARLARI (SARI ZEMİN - SİYAH YAZI - KONTRAST TASARIM) ---
st.markdown("""
    <style>
    /* 1. Arka Planı Canlı SARI Yap */
    .stApp {
        background-color: #FFF59D !important; /* Okunabilir Tatlı Sarı */
    }
    
    /* 2. Tüm Yazıları Simsiyah ve Kalın Yap */
    h1, h2, h3, h4, h5, h6, p, div, span, label, li, .stMarkdown, .stRadio label {
        color: #000000 !important;
        font-family: 'Arial', sans-serif;
    }
    
    /* 3. Şık Butonları (Beyaz Zemin, Siyah Yazı, Sarı Kenarlık) */
    .stButton>button { 
        width: 100%; 
        border-radius: 12px; 
        min-height: 4.5em; 
        font-weight: 700; 
        background-color: #FFFFFF !important; 
        color: #000000 !important; 
        border: 3px solid #FBC02D !important; /* Koyu Sarı Çerçeve */
        white-space: pre-wrap; 
        text-align: left !important; 
        padding: 15px;
        transition: all 0.3s ease;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    
    /* Üzerine gelince */
    .stButton>button:hover { 
        background-color: #FFEB3B !important; /* Daha koyu sarı */
        border-color: #000000 !important; 
        transform: scale(1.01);
    }
    
    /* 4. Giriş Kutuları */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important; 
        color: #000000 !important; 
        border: 2px solid #000000 !important;
        font-weight: bold;
    }
    
    /* 5. Soru Metni */
    .big-font { 
        font-size: 24px !important; 
        font-weight: 900; 
        color: #000000 !important; 
        margin-bottom: 25px;
        padding: 15px;
        background-color: rgba(255,255,255,0.4);
        border-radius: 10px;
        border-left: 5px solid #000;
    }
    
    /* İlerleme Çubuğu Rengi */
    .stProgress > div > div > div > div {
        background-color: #000000 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 1. MÜFREDAT LİSTESİ ---
MUFREDAT = {
    "9. Sınıf": ["Temel Muhasebe", "Mesleki Matematik", "Ofis Uygulamaları", "Mesleki Gelişim Atölyesi"],
    "10. Sınıf": ["Genel Muhasebe", "Temel Hukuk", "Ekonomi", "Klavye Teknikleri"],
    "11. Sınıf": [
        "Bilgisayarlı Muhasebe (Luca)", 
        "Maliyet Muhasebesi", 
        "Şirketler Muhasebesi", 
        "Vergi ve Beyannameler", 
        "İş ve Sosyal Güvenlik Hukuku", 
        "Girişimcilik ve İşletme"
    ],
    "12. Sınıf": [
        "Dış Ticaret", 
        "Kooperatifçilik", 
        "Hızlı Klavye", 
        "Ahilik Kültürü ve Girişimcilik"
    ]
}

# --- 2. DETAYLI KONU HAVUZU (YILLIK PLANLARDAN ÇEKİLDİ) ---
# Yapay Zeka bu konuları karıştırarak soracak.
KONU_HAVUZU = {
    "Temel Hukuk": ["Hukukun Kaynakları (Yazılı/Yazısız)", "Hak Ehliyeti ve Fiil Ehliyeti", "Kişilik Kavramı (Gerçek/Tüzel)", "Borcun Unsurları (Alacaklı, Borçlu, Edim)", "Sözleşme Çeşitleri", "Haksız Fiil ve Sebepsiz Zenginleşme", "Mülkiyet Hakkı", "Tacir ve Esnaf Ayrımı", "Kıymetli Evrak (Bono, Çek, Poliçe)", "Sigorta Türleri (Can, Mal, Sorumluluk)"],
    "Ekonomi": ["Fayda ve Değer Kavramları", "Üretim Faktörleri (Emek, Sermaye, Doğal Kaynak)", "Arz ve Talep Kanunu", "Piyasa Dengesi ve Fiyat", "Tam Rekabet ve Tekel Piyasaları", "Enflasyon ve Deflasyon", "Milli Gelir (GSYİH)", "Merkez Bankası ve Para Politikası", "Ödemeler Dengesi", "Uluslararası Kuruluşlar (IMF, Dünya Bankası)"],
    "Genel Muhasebe": ["Bilanço Temel Denkliği", "Dönen ve Duran Varlıklar", "Kısa ve Uzun Vadeli Yabancı Kaynaklar", "Özkaynaklar", "Gelir Tablosu İlkeleri", "Tek Düzen Hesap Planı Kodları", "Yevmiye Defteri Borç/Alacak Mantığı", "Büyük Defter (Defter-i Kebir)", "Mizan (Geçici ve Kesin)", "Satılan Ticari Mallar Maliyeti"],
    "Temel Muhasebe": ["Fatura ve İrsaliye Ayrımı", "Yazar Kasa Fişi Sınırları", "Gider Pusulası Kullanımı", "Serbest Meslek Makbuzu", "İşletme Defteri Gider Kaydı", "İşletme Defteri Gelir Kaydı", "Vergi Dairesi Mükellefiyet", "Defter Saklama Süreleri"],
    "Mesleki Matematik": ["Yüzde Hesapları", "Maliyet ve Satış Fiyatı", "KDV Hariç/Dahil Hesaplama", "İskonto (İndirim) Hesapları", "Basit Faiz Hesabı", "Kar/Zarar Problemleri"],
    "Ofis Uygulamaları": ["Word Biçimlendirme", "Excel Hücre Adresleri", "Excel Topla/Ortalama Formülleri", "Excel Eğer Formülü", "PowerPoint Animasyonları", "Klavye Kısayolları (CTRL+C, CTRL+V)"],
}

# --- 3. DEVASA YEDEK DEPO (TEKRARI ÖNLEMEK İÇİN SABİT SORULAR) ---
# Yapay Zeka çalışmazsa buradan çekecek. Her derse özel 10-15 soru var.
YEDEK_DEPO = {
    "Temel Hukuk": [
        {"soru": "Aşağıdakilerden hangisi hukukun yazılı kaynaklarından biri değildir?", "secenekler": ["Anayasa", "Kanun", "Yönetmelik", "Örf ve Adet", "Cumhurbaşkanlığı Kararnamesi"], "cevap": "Örf ve Adet"},
        {"soru": "Hak ehliyeti ne zaman başlar?", "secenekler": ["Sağ ve tam doğmak koşuluyla ana rahmine düşüldüğü an", "18 yaşını doldurunca", "Doğumdan 1 hafta sonra", "Okula başlayınca", "Evlenince"], "cevap": "Sağ ve tam doğmak koşuluyla ana rahmine düşüldüğü an"},
        {"soru": "Bir kimsenin borcunu ödememesi durumunda alacaklının devlet gücüyle alacağını tahsil etmesine ne denir?", "secenekler": ["Cebri İcra", "Tazminat", "Hapis", "Müsadere", "Vergi"], "cevap": "Cebri İcra"},
        {"soru": "Aşağıdakilerden hangisi Borcun unsurlarından biridir?", "secenekler": ["Edim", "Hakim", "Savcı", "Tapu", "Noter"], "cevap": "Edim"},
        {"soru": "Tacir sıfatını kazanmak için temel şart nedir?", "secenekler": ["Bir ticari işletmeyi kısmen de olsa kendi adına işletmek", "18 yaşını doldurmak", "Zengin olmak", "Şirket ortağı olmak", "Dükkan kiralamak"], "cevap": "Bir ticari işletmeyi kısmen de olsa kendi adına işletmek"},
        {"soru": "Çek üzerinde yazılı olan ve ödeme gününü belirten tarihe ne ad verilir?", "secenekler": ["Keşide Tarihi", "Vade", "Tanzim", "Ciro", "Aval"], "cevap": "Keşide Tarihi"},
        {"soru": "Hangisi bir 'Özel Hukuk' dalıdır?", "secenekler": ["Medeni Hukuk", "İdare Hukuku", "Vergi Hukuku", "Ceza Hukuku", "Anayasa Hukuku"], "cevap": "Medeni Hukuk"}
    ],
    "Ekonomi": [
        {"soru": "İnsan ihtiyaçlarını karşılayan mal ve hizmetlerin miktarının, insan ihtiyaçlarına göre az olmasına ne denir?", "secenekler": ["Kıtlık", "Bolluk", "Enflasyon", "Deflasyon", "Fayda"], "cevap": "Kıtlık"},
        {"soru": "Bir malın fiyatı arttığında talebinin azalması, fiyatı düştüğünde talebinin artması neyi ifade eder?", "secenekler": ["Talep Kanunu", "Arz Kanunu", "Fırsat Maliyeti", "Marjinal Fayda", "Üretim"], "cevap": "Talep Kanunu"},
        {"soru": "Paranın değerinin düşmesi ve fiyatlar genel seviyesinin sürekli artmasına ne ad verilir?", "secenekler": ["Enflasyon", "Devalüasyon", "Resesyon", "Deflasyon", "Stagflasyon"], "cevap": "Enflasyon"},
        {"soru": "Aşağıdakilerden hangisi Üretim Faktörlerinden biri değildir?", "secenekler": ["Para", "Emek (İşgücü)", "Sermaye", "Doğal Kaynaklar", "Girişimci"], "cevap": "Para"},
        {"soru": "Türkiye Cumhuriyet Merkez Bankasının temel amacı nedir?", "secenekler": ["Fiyat İstikrarını Sağlamak", "Kar Etmek", "Kredi Vermek", "Döviz Satmak", "Maaş Dağıtmak"], "cevap": "Fiyat İstikrarını Sağlamak"}
    ],
    "Genel Muhasebe": [
        {"soru": "Bilanço eşitliği aşağıdakilerden hangisidir?", "secenekler": ["Varlıklar = Yabancı Kaynaklar + Özkaynaklar", "Aktif = Giderler", "Borç = Alacak", "Gelir = Gider", "Kasa = Banka"], "cevap": "Varlıklar = Yabancı Kaynaklar + Özkaynaklar"},
        {"soru": "İşletmenin kasasına nakit para girdiğinde '100 Kasa' hesabı nasıl çalışır?", "secenekler": ["Borçlanır", "Alacaklanır", "Kapanır", "Bakiyesi Silinir", "Pasife Yazılır"], "cevap": "Borçlanır"},
        {"soru": "Satıcıya olan veresiye borçlar hangi hesapta izlenir?", "secenekler": ["320 Satıcılar", "120 Alıcılar", "100 Kasa", "102 Bankalar", "600 Satışlar"], "cevap": "320 Satıcılar"},
        {"soru": "Tek düzen hesap planında '6' ile başlayan hesap grubu nedir?", "secenekler": ["Gelir Tablosu Hesapları", "Dönen Varlıklar", "Duran Varlıklar", "Özkaynaklar", "Maliyet Hesapları"], "cevap": "Gelir Tablosu Hesapları"},
        {"soru": "Dönem sonunda '600 Yurt İçi Satışlar' hesabı hangi hesaba devredilerek kapatılır?", "secenekler": ["690 Dönem Karı veya Zararı", "100 Kasa", "500 Sermaye", "320 Satıcılar", "120 Alıcılar"], "cevap": "690 Dönem Karı veya Zararı"}
    ],
    "Genel": [
        {"soru": "Excel'de 'Toplama' işlemini yapan formül hangisidir?", "secenekler": ["=TOPLA()", "=ÇIKAR()", "=SAY()", "=EĞER()", "=ORTALAMA()"], "cevap": "=TOPLA()"},
        {"soru": "Word programında 'Kaydet' kısayolu nedir?", "secenekler": ["CTRL + S", "CTRL + P", "CTRL + C", "CTRL + V", "CTRL + Z"], "cevap": "CTRL + S"},
        {"soru": "KDV hariç 100 TL olan bir ürünün %20 KDV dahil fiyatı nedir?", "secenekler": ["120 TL", "100 TL", "118 TL", "110 TL", "102 TL"], "cevap": "120 TL"}
    ]
}

# --- AI AYARLARI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def yapay_zeka_soru_uret(sinif, ders):
    ai_sorulari = []
    
    # 1. KONU SEÇİMİ (HAVUZDAN RASTGELE KONULAR ÇEKİLİR)
    # Bu sayede her seferinde farklı bir haftanın konusu gelir.
    tum_konular = KONU_HAVUZU.get(ders, ["Genel Konular"])
    
    # Rastgele 3 konu seç
    secilen_konular = random.sample(tum_konular, min(3, len(tum_konular)))
    konu_metni = ", ".join(secilen_konular)
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # --- KESİN PROMPT ---
        prompt = f"""
        Rolün: Lise Öğretmeni.
        Ders: {ders} (Sınıf: {sinif}).
        
        GÖREV: Aşağıdaki Konu Başlıklarından 10 ADET ÖZGÜN test sorusu hazırla.
        SEÇİLEN KONULAR: {konu_metni}
        
        KURALLAR:
        1. Sorular {sinif} seviyesine uygun ve MEB müfredatıyla uyumlu olsun.
        2. Her sorunun 5 şıkkı (A,B,C,D,E) olsun.
        3. Cevaplar şıklara rastgele dağılsın (Hepsi A olmasın).
        4. "Aşağıdakilerden hangisi" kalıbını sık kullanma, olay örgüsü kur.
        5. Çıktı SADECE JSON formatında olsun.
        
        JSON FORMATI:
        [ {{ "soru": "Soru metni...", "secenekler": ["Şık1", "Şık2", "Şık3", "Şık4", "Şık5"], "cevap": "Doğru şıkkın tam metni" }} ]
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

    # 2. YEDEKLEME (Eğer AI çalışmazsa devreye girer)
    if len(ai_sorulari) < 10:
        # Önce derse özel yedeği dene, yoksa genele bak
        yedek = YEDEK_DEPO.get(ders, YEDEK_DEPO["Genel"])
        eksik = 10 - len(ai_sorulari)
        
        # Yedeği karıştırarak al
        random.shuffle(yedek)
        ai_sorulari.extend(yedek[:eksik])
            
    # 3. ŞIKLARI VE SORULARI KARIŞTIR
    random.shuffle(ai_sorulari) # Soruların sırasını karıştır
    for soru in ai_sorulari:
        random.shuffle(soru["secenekler"]) # Şıkları karıştır
    
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
    
    col_a, col_b = st.columns(2)
    with col_a:
        secilen_sinif = st.selectbox("Sınıfınız:", list(MUFREDAT.keys()))
    with col_b:
        dersler = MUFREDAT[secilen_sinif]
        secilen_ders = st.selectbox("Ders Seçiniz:", dersler)
    
    st.write("---")
    
    with st.form("giris_formu"):
        st.write("### 🎓 Öğrenci Bilgileri")
        col1, col2 = st.columns(2)
        ad = col1.text_input("Adınız")
        soyad = col2.text_input("Soyadınız")
        st.write("")
        btn = st.form_submit_button("Sınavı Başlat 🚀")
        
        if btn:
            if ad and soyad:
                st.session_state.kimlik = {"ad": ad, "soyad": soyad, "sinif": secilen_sinif, "ders": secilen_ders}
                st.session_state.yukleniyor = True
                st.rerun()
            else:
                st.warning("Lütfen Ad ve Soyad giriniz.")

    if st.session_state.yukleniyor:
        with st.status(f"Sorular Hazırlanıyor... ({st.session_state.kimlik['ders']})", expanded=True):
            sorular = yapay_zeka_soru_uret(st.session_state.kimlik['sinif'], st.session_state.kimlik['ders'])
            
            if not sorular: # Hiç soru gelmezse
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
    <div style='background-color:#FFEB3B; padding:20px; border-radius:15px; text-align:center; border: 3px solid #000; box-shadow: 5px 5px 0px #000;'>
        <h2>{st.session_state.kimlik['ad']} {st.session_state.kimlik['soyad']}</h2>
        <h1>PUAN: {st.session_state.puan}</h1>
        <p><b>{st.session_state.kimlik['sinif']} - {st.session_state.kimlik['ders']}</b></p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.kayit_ok:
        with st.spinner("Sonuç öğretmene gönderiliyor..."):
            res = sonuclari_kaydet(
                st.session_state.kimlik["ad"], st.session_state.kimlik["soyad"],
                st.session_state.kimlik["sinif"], st.session_state.kimlik["ders"],
                st.session_state.puan
            )
            if res:
                st.success("Sonuç Kaydedildi ✅")
                st.session_state.kayit_ok = True
            else:
                st.error("Bağlantı Hatası: Sonuç kaydedilemedi.")
    
    st.write("")
    if st.button("Çıkış Yap"):
        st.session_state.oturum_basladi = False
        st.rerun()
