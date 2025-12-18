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

# --- 1. MÜFREDAT LİSTESİ (Yıllık Planlarınızdaki Tüm Dersler) ---
MUFREDAT = {
    "9. Sınıf": ["Temel Muhasebe", "Mesleki Matematik", "Ofis Uygulamaları", "Mesleki Gelişim Atölyesi"],
    "10. Sınıf": ["Finansal Muhasebe", "Temel Hukuk", "Temel Ekonomi", "Klavye Teknikleri"],
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

# --- 2. DETAYLI KONU HAVUZU (YILLIK PLANLARDAN ÇEKİLENLER) ---
# Sistem buradan her seferinde rastgele 3 konu seçip soruyu ona göre üretecek.
KONU_HAVUZU = {
    # --- 9. SINIF ---
    "Temel Muhasebe": [
        "Ticari Defter ve Belgeler", "Fatura ve İrsaliye Düzenleme", "Perakende Satış Fişi ve Yazar Kasa",
        "Gider Pusulası ve Müstahsil Makbuzu", "Serbest Meslek Makbuzu", "İşletme Hesabı Defteri Gider Kayıtları",
        "İşletme Hesabı Defteri Gelir Kayıtları", "Vergi Dairesi İşlemleri ve Bildirimler", "Belediye İşlemleri (Ruhsat vb.)"
    ],
    "Mesleki Matematik": [
        "Yüzde Hesaplamaları", "Binde Hesaplamaları", "Maliyet ve Satış Fiyatı Hesaplama",
        "KDV Hesaplamaları (Hariç ve Dahil)", "Ticari Belgelerde Tutar Hesaplama", 
        "Basit İskonto Hesaplamaları (İç ve Dış)", "Karışım ve Alaşım Problemleri", "Faiz Hesaplamaları"
    ],
    "Ofis Uygulamaları": [
        "Kelime İşlemci (Word) Sekmeler ve Şeritler", "Metin Biçimlendirme ve Yazı Tipi",
        "Word'de Tablo ve Resim Ekleme", "Elektronik Tablolama (Excel) Hücre Yapısı",
        "Excel Formülleri (Topla, Ortalama, Eğer, Mak, Min)", "Excel'de Grafik Oluşturma",
        "Sunu Hazırlama (PowerPoint) Slayt Tasarımı", "Slayt Geçişleri ve Animasyonlar"
    ],
    "Mesleki Gelişim Atölyesi": [
        "Ahilik Kültürü ve Meslek Etiği", "İletişim Süreci ve Türleri", "Etkili İletişim Teknikleri",
        "İş Sağlığı ve Güvenliği Tedbirleri", "Girişimcilik Fikirleri ve İnovasyon",
        "Kişisel Gelişim ve Kariyer Planlama", "Teknolojik Gelişmeler ve Meslekler"
    ],

    # --- 10. SINIF ---
    "Finansal Muhasebe": [
        "Muhasebe Temel Kavramları", "Bilanço Eşitliği ve İlkeleri", "Varlık Hesapları (100-299)",
        "Kaynak Hesapları (300-599)", "Yevmiye Defteri Kayıt Kuralları", "Büyük Defter (Defter-i Kebir) Aktarımı",
        "Mizan Düzenleme (Geçici ve Kesin Mizan)", "7/A ve 7/B Maliyet Seçenekleri", "Nazım Hesapların İşleyişi"
    ],
    "Temel Hukuk": [
        "Hukukun Temel Kaynakları", "Hak Kavramı ve Türleri", "Kişiler Hukuku (Gerçek ve Tüzel Kişiler)",
        "Borçlar Hukuku ve Sözleşmeler", "Mülkiyet Hakkı", "Yargı Sistemi ve Dava Türleri",
        "Sigorta Hukuku (Can ve Mal Sigortaları)"
    ],
    "Temel Ekonomi": [
        "Ekonomik Sistemler", "Arz ve Talep Kanunları", "Piyasa Dengesi ve Fiyat Oluşumu",
        "Enflasyon, Deflasyon ve Devalüasyon", "Milli Gelir Kavramları", "Para ve Bankacılık",
        "Uluslararası Ekonomik Kuruluşlar", "Türkiye-AB İlişkileri"
    ],
    "Klavye Teknikleri": [
        "F Klavye Temel Sıra Tuşları (A, K, E, M...)", "Üst ve Alt Sıra Tuşları", "Rakam ve Sembol Tuşları",
        "Oturuş ve Duruş Teknikleri", "Süreli Metin Yazma Çalışmaları", "Hatasız Yazım Teknikleri"
    ],

    # --- 11. SINIF ---
    "Bilgisayarlı Muhasebe (Luca)": [
        "Muhasebe Programı Kurulumu ve Şirket Açma", "Stok Kartı ve Cari Kart Tanımlama",
        "Alış ve Satış Faturası İşleme", "Muhasebe Fişleri (Tahsil, Tediye, Mahsup)",
        "Çek ve Senet Modülü İşlemleri", "Banka Hareketleri Kaydı", "KDV Beyannamesi Alma", "Dönem Sonu Devir İşlemleri"
    ],
    "Maliyet Muhasebesi": [
        "Gider, Harcama ve Maliyet Kavramları", "Direkt İlk Madde ve Malzeme Giderleri (150)",
        "Direkt İşçilik Giderleri (720)", "Genel Üretim Giderleri (730)", "7A ve 7B Maliyet Seçenekleri",
        "Satılan Mamul Maliyeti Tablosu", "Hizmet Üretim Maliyeti"
    ],
    "Şirketler Muhasebesi": [
        "Şahıs ve Sermaye Şirketleri", "Kolektif Şirket Kuruluşu", "Anonim Şirket Kuruluş Kayıtları",
        "Sermaye Artırımı İşlemleri", "Sermaye Azaltımı İşlemleri", "Kar Dağıtımı ve Yedek Akçeler",
        "Şirket Birleşmeleri ve Devir", "Şirketlerde Tasfiye Süreci"
    ],
    "Vergi ve Beyannameler": [
        "Vergi Hukuku ve Verginin Tarafları", "Gelir Vergisi Beyannamesi", "Kurumlar Vergisi Beyannamesi",
        "Katma Değer Vergisi (KDV)", "Özel Tüketim Vergisi (ÖTV)", "Motorlu Taşıtlar Vergisi (MTV)",
        "Muhtasar ve Prim Hizmet Beyannamesi"
    ],
    "İş ve Sosyal Güvenlik Hukuku": [
        "4857 Sayılı İş Kanunu", "İş Sözleşmesi Türleri", "Ücret ve Ücret Bordrosu Hesaplama",
        "Kıdem ve İhbar Tazminatı", "Yıllık İzin Hakları", "İş Sağlığı ve Güvenliği Mevzuatı",
        "Sosyal Sigortalar ve GSS (4a, 4b, 4c)"
    ],
    "Girişimcilik ve İşletme": [
        "Girişimcilik Özellikleri ve Türleri", "İş Planı (Business Plan) Hazırlama",
        "Fizibilite Raporu (Yapılabilirlik)", "Pazar Araştırması", "Pazarlama Stratejileri",
        "KOSGEB ve Devlet Destekleri", "İnovasyon ve Yaratıcılık"
    ],

    # --- 12. SINIF ---
    "Dış Ticaret": [
        "İhracat ve İthalat Rejimi", "Teslim Şekilleri (Incoterms - FOB, CIF, EXW)",
        "Ödeme Şekilleri (Akreditif, Peşin, Vesaik Mukabili)", "Gümrük Mevzuatı ve Belgeler",
        "Kambiyo İşlemleri", "Serbest Bölgeler", "Dış Ticaret Finansmanı"
    ],
    "Kooperatifçilik": [
        "Kooperatifçilik İlkeleri", "Kooperatif Kuruluş İşlemleri ve Ana Sözleşme",
        "Ortaklık Hak ve Ödevleri", "Kooperatif Organları (Genel Kurul, Yönetim)",
        "Risturn (Kar Payı) Dağıtımı", "Kooperatiflerde Tasfiye"
    ],
    "Hızlı Klavye": [
        "İleri Seviye Metin Yazma", "Dikte Çalışmaları", "Adli ve Hukuki Metin Yazımı",
        "Resmi Yazışma Kuralları", "Rapor ve Tutanak Düzenleme"
    ],
    "Ahilik Kültürü ve Girişimcilik": [
        "Ahilik Teşkilatı ve Fütüvvetnameler", "Ahilikte Meslek Ahlakı ve İlkeler",
        "Usta-Çırak İlişkisi ve Şed Kuşanma", "Günümüz Esnaf Teşkilatları",
        "Girişimcilikte Etik Değerler", "E-Ticaret ve Dijital Girişimcilik"
    ]
}

# --- YEDEK DEPO (ACİL DURUM) ---
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
    
    # 1. KONU SEÇİMİ (HAVUZDAN RASTGELE KONULAR ÇEKİLİR)
    # Bu sayede her seferinde farklı bir haftanın konusu gelir.
    tum_konular = KONU_HAVUZU.get(ders, ["Genel Konular"])
    # Listeden rastgele 2 veya 3 konu seç
    secilen_konular = random.sample(tum_konular, min(3, len(tum_konular)))
    konu_metni = ", ".join(secilen_konular)
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # --- PROMPT ---
        prompt = f"""
        Rolün: Lise Öğretmeni.
        Ders: {ders} (Sınıf: {sinif}).
        
        GÖREV: Aşağıdaki Yıllık Plan Konularından 10 ADET özgün test sorusu hazırla.
        SEÇİLEN KONULAR: {konu_metni}
        
        KURALLAR:
        1. Sorular {sinif} seviyesine uygun ve MEB müfredatıyla uyumlu olsun.
        2. Her sorunun 5 şıkkı (A,B,C,D,E) olsun.
        3. Cevaplar şıklara rastgele dağılsın.
        4. Sorular seçilen konulara odaklanmalı.
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

    # 2. YEDEKLEME
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
        with st.status(f"Yıllık Plandan Konular Seçiliyor... ({st.session_state.kimlik['ders']})", expanded=True):
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
