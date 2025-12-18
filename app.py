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

# --- GÖRÜNTÜ AYARLARI ---
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
    .big-font { font-size: 20px !important; font-weight: 700; color: #111827 !important; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 1. MÜFREDAT LİSTESİ ---
MUFREDAT = {
    "9. Sınıf": ["Temel Muhasebe", "Mesleki Matematik", "Ofis Uygulamaları", "Mesleki Gelişim Atölyesi"],
    "10. Sınıf": ["Genel Muhasebe", "Temel Hukuk", "Ekonomi", "Klavye Teknikleri"],
    "11. Sınıf": ["Bilgisayarlı Muhasebe", "Maliyet Muhasebesi", "Şirketler Muhasebesi", "Vergi ve Beyannameler", "İş ve Sosyal Güvenlik Hukuku", "Girişimcilik ve İşletme"],
    "12. Sınıf": ["Dış Ticaret", "Kooperatifçilik", "Hızlı Klavye", "Ahilik Kültürü ve Girişimcilik"]
}

# --- 2. YILLIK PLANLARDAN ÇEKİLEN DETAYLI KONU HAVUZU ---
# Bu kısım yüklediğiniz Excel dosyalarından özel olarak çıkarılmıştır.
KONU_DETAYLARI = {
    # 9. SINIF
    "Temel Muhasebe": "Ticari Defter ve Belgeler, Fatura ve İrsaliye Düzenleme, Perakende Satış Fişi, İşletme Hesabı Defteri Gider ve Gelir Kayıtları, İşletme Hesabı Özeti, Vergi Dairesi ve Belediye İşlemleri, Serbest Meslek Kazanç Defteri.",
    "Mesleki Matematik": "Kolay Hesaplama Teknikleri, Değer ve Değerleme Kavramları, Yüzde ve Binde Hesapları, Maliyet ve Satış Fiyatı Hesaplama, Basit İç ve Dış İskonto, KDV Hesaplamaları, Karışım ve Alaşım Problemleri.",
    "Ofis Uygulamaları": "Kelime İşlemci (Word) Paragraf ve Tablo İşlemleri, Elektronik Tablolama (Excel) Formüller (Topla, Ortalama, Eğer), Sunu Hazırlama (PowerPoint) Slayt Tasarımı ve Animasyonlar, Yazıcı Ayarları.",
    "Mesleki Gelişim Atölyesi": "Meslek Etiği ve Ahilik İlkeleri, İletişim Süreci ve Türleri, İş Sağlığı ve Güvenliği Tedbirleri, Girişimcilik Fikirleri, Telif ve Patent Hakları, Kişisel Gelişim.",

    # 10. SINIF
    "Genel Muhasebe": "Muhasebe Temel Kavramları, Bilanço Eşitliği, Yevmiye Defteri Kayıt Kuralları, Büyük Defter Aktarımı, Mizan Düzenleme, 7/A ve 7/B Maliyet Seçenekleri, Nazım Hesapların İşleyişi, Dönem Sonu Envanter İşlemleri.",
    "Temel Hukuk": "Hukukun Kaynakları, Hak Kavramı ve Türleri, Kişiler Hukuku (Gerçek ve Tüzel Kişiler), Borçlar Hukuku ve Sözleşmeler, Mülkiyet Hakkı, Yargı Sistemi, Sigorta Hukuku (Can ve Mal Sigortaları).",
    "Ekonomi": "Ekonomik Sistemler, Arz ve Talep Kanunları, Piyasa Dengesi, Enflasyon ve Devalüasyon, Milli Gelir, Para ve Bankacılık, Uluslararası Ekonomik Kuruluşlar, Türkiye-AB İlişkileri.",
    "Klavye Teknikleri": "F Klavye Temel Sıra Tuşları, Üst ve Alt Sıra, Rakam ve Semboller, Oturuş Düzeni, Süreli Metin Yazma, Hatasız Yazım Teknikleri, Hukuki Metin Yazımı.",

    # 11. SINIF
    "Bilgisayarlı Muhasebe": "Paket Program Kurulumu, Şirket Açma, Stok ve Cari Kart Tanımlama, Fatura ve İrsaliye İşleme, Muhasebe Fişleri (Tahsil, Tediye, Mahsup), Çek/Senet Modülü, Banka İşlemleri, KDV Beyannamesi Alma.",
    "Maliyet Muhasebesi": "Gider, Harcama ve Maliyet Kavramları, 7A ve 7B Seçenekleri, Direkt İlk Madde ve Malzeme Giderleri (150), Direkt İşçilik (720), Genel Üretim Giderleri (730), Satılan Mamul Maliyeti Tablosu.",
    "Şirketler Muhasebesi": "Şirket Türleri (Şahıs ve Sermaye), Şirket Kuruluş Kayıtları, Sermaye Artırımı ve Azaltımı, Kar Dağıtımı, Yedek Akçeler, Şirket Birleşmeleri ve Devir, Tasfiye Süreci ve Kayıtları.",
    "Vergi ve Beyannameler": "Vergi Hukuku Kavramları, Gelir Vergisi, Kurumlar Vergisi, Katma Değer Vergisi (KDV), Özel Tüketim Vergisi (ÖTV), Motorlu Taşıtlar Vergisi (MTV), Muhtasar Beyanname Düzenleme.",
    "İş ve Sosyal Güvenlik Hukuku": "4857 Sayılı İş Kanunu, İş Sözleşmesi Türleri, Kıdem ve İhbar Tazminatı Hesaplama, Yıllık İzinler, İş Sağlığı ve Güvenliği, SGK 4/a, 4/b, 4/c Kavramları, Genel Sağlık Sigortası.",
    "Girişimcilik ve İşletme": "Girişimcilik Türleri, İş Planı (Business Plan) Hazırlama, Fizibilite Raporu, Pazar Araştırması, Pazarlama Karması, KOSGEB Destekleri, İnovasyon.",

    # 12. SINIF
    "Dış Ticaret": "Dış Ticaret Rejimi, İhracat ve İthalat Süreçleri, Teslim Şekilleri (FOB, CIF, EXW), Ödeme Şekilleri (Akreditif, Peşin), Gümrük Mevzuatı, Kambiyo İşlemleri, Serbest Bölgeler.",
    "Kooperatifçilik": "Kooperatifçilik İlkeleri, Kooperatif Kuruluş İşlemleri, Ana Sözleşme, Ortaklık Hakları, Genel Kurul ve Yönetim Kurulu Görevleri, Risturn Hesaplama, Tasfiye.",
    "Hızlı Klavye": "İleri Seviye Metin Yazma, Dikte Çalışmaları, Adli ve Hukuki Metin Yazımı, Resmi Yazışma Kuralları, Raporlama Teknikleri.",
    "Ahilik Kültürü ve Girişimcilik": "Ahilik Teşkilatı ve İlkeleri, Meslek Ahlakı, Fütüvvetnameler, Günümüz Esnaf Teşkilatları, Girişimcilikte Etik Değerler, E-Ticaret ve Dijital Girişimcilik."
}

# --- YEDEK DEPO (ACİL DURUM İÇİN STANDART SORULAR) ---
YEDEK_DEPO = {
    "Genel": [
        {"soru": "VUK'a göre fatura düzenleme sınırı (2025) aşıldığında hangi belge düzenlenmelidir?", "secenekler": ["Fatura", "Fiş", "Gider Pusulası", "İrsaliye", "Dekont"], "cevap": "Fatura"},
        {"soru": "Bilanço temel denkliği hangisidir?", "secenekler": ["Varlıklar = Kaynaklar", "Gelir = Gider", "Borç = Alacak", "Aktif = Pasif + Sermaye", "Kasa = Banka"], "cevap": "Varlıklar = Kaynaklar"},
        {"soru": "Excel'de 'EĞER' formülü ne işe yarar?", "secenekler": ["Mantıksal kıyaslama yapar", "Toplama yapar", "Ortalama alır", "Yazı rengini değiştirir", "Tablo çizer"], "cevap": "Mantıksal kıyaslama yapar"}
    ]
}

# --- AI AYARLARI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def yapay_zeka_soru_uret(sinif, ders):
    ai_sorulari = []
    
    # YILLIK PLANDAN KONUYU AL
    konu_kapsami = KONU_DETAYLARI.get(ders, "Genel Müfredat Konuları")
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # --- KESİN PROMPT ---
        prompt = f"""
        Rolün: Lise Muhasebe ve Finansman Öğretmeni.
        Ders: {ders} (Sınıf Seviyesi: {sinif}).
        
        Aşağıdaki Yıllık Plan Konularına SADIK KALARAK 10 ADET test sorusu hazırla:
        MÜFREDAT KONULARI: {konu_kapsami}
        
        KURALLAR:
        1. Sorular {sinif} seviyesine uygun ve MEB müfredatıyla uyumlu olsun.
        2. Her sorunun 5 şıkkı (A,B,C,D,E) olsun.
        3. Cevaplar şıklara rastgele dağılsın.
        4. "Yukarıdakilerden hangisi" gibi sorular yerine doğrudan bilgi veya analiz sorusu sor.
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

    # YEDEKLEME
    if len(ai_sorulari) < 10:
        yedek = YEDEK_DEPO["Genel"]
        eksik = 10 - len(ai_sorulari)
        ai_sorulari.extend(random.choices(yedek, k=eksik))
            
    # ŞIKLARI KARIŞTIR
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
        with st.status(f"Yıllık Plandan Sorular Hazırlanıyor... ({st.session_state.kimlik['ders']})", expanded=True):
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
