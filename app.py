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

# --- GÖRÜNTÜ AYARLARI (Zorla Beyaz Ekran) ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    h1, h2, h3, h4, h5, h6, p, div, span, label, li { color: #000000 !important; }
    .stButton>button { 
        width: 100%; border-radius: 12px; height: auto; min-height: 3.5em; 
        font-weight: bold; background-color: #f0f2f6 !important; 
        color: #000000 !important; border: 2px solid #d1d5db !important;
        white-space: pre-wrap;
    }
    .stButton>button:hover { background-color: #e5e7eb !important; border-color: #000000 !important; }
    .big-font { font-size: 20px !important; font-weight: 700; color: #111827 !important; margin-bottom: 20px; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #ffffff !important; color: #000000 !important; border-color: #9ca3af !important;
    }
    .stStatus { background-color: #ffffff !important; border: 1px solid #ddd; }
    </style>
""", unsafe_allow_html=True)

# --- DERS MÜFREDATI ---
MUFREDAT = {
    "9. Sınıf": ["Temel Muhasebe", "Mesleki Gelişim Atölyesi", "Mesleki Matematik", "Ofis Uygulamaları"],
    "10. Sınıf": ["Finansal Muhasebe", "Temel Hukuk", "Temel Ekonomi", "Klavye Teknikleri"],
    "11. Sınıf": ["Maliyet Muhasebesi", "Şirketler Muhasebesi", "Bilgisayarlı Muhasebe (Luca)", "Bilgisayarlı Muhasebe (ETA SQL)"],
    "12. Sınıf": ["Bankacılık ve Finans", "Finansal Okuryazarlık"]
}

# --- YEDEK SORU DEPOSU (MÜFREDATA UYGUN) ---
# AI çalışmazsa devreye girer. Her ders için en az 5-10 soru var.
YEDEK_DEPO = {
    # 9. SINIF - YENİ MÜFREDAT
    "Temel Muhasebe": [
        {"soru": "Aşağıdakilerden hangisi Fatura yerine geçen belgelerden biridir?", "secenekler": ["Perakende Satış Fişi", "Bilanço", "Mizan"], "cevap": "Perakende Satış Fişi"},
        {"soru": "Malın bir yerden bir yere taşınması sırasında düzenlenen belge hangisidir?", "secenekler": ["Sevk İrsaliyesi", "Fatura", "Gider Pusulası"], "cevap": "Sevk İrsaliyesi"},
        {"soru": "İşletme Hesabı Defterinin sol tarafına ne kaydedilir?", "secenekler": ["Giderler", "Gelirler", "Karlar"], "cevap": "Giderler"},
        {"soru": "Serbest meslek erbabının (Doktor, Avukat vb.) düzenlediği belge nedir?", "secenekler": ["Serbest Meslek Makbuzu", "Fatura", "Müstahsil Makbuzu"], "cevap": "Serbest Meslek Makbuzu"},
        {"soru": "Vergi levhası nereden alınır?", "secenekler": ["Vergi Dairesi (GİB)", "Belediye", "Muhtarlık"], "cevap": "Vergi Dairesi (GİB)"},
        {"soru": "Çiftçiden ürün alırken düzenlenen belge hangisidir?", "secenekler": ["Müstahsil Makbuzu", "Gider Pusulası", "Fatura"], "cevap": "Müstahsil Makbuzu"},
        {"soru": "Vergi hatası düzeltme, yoklama gibi işlemler hangi kurumla ilgilidir?", "secenekler": ["Vergi Dairesi", "SGK", "Belediye"], "cevap": "Vergi Dairesi"},
        {"soru": "İş yeri açma ve çalışma ruhsatı nereden alınır?", "secenekler": ["Belediye", "Vergi Dairesi", "Bankalar"], "cevap": "Belediye"},
        {"soru": "Sigortalı işe giriş bildirgesi hangi kuruma verilir?", "secenekler": ["SGK", "İŞKUR", "Maliye"], "cevap": "SGK"},
        {"soru": "Defter tutma hadleri her yıl kim tarafından belirlenir?", "secenekler": ["Hazine ve Maliye Bakanlığı", "Belediyeler", "Valilik"], "cevap": "Hazine ve Maliye Bakanlığı"}
    ],
    
    # 10. SINIF - FİNANSAL MUHASEBE (Eski Temel Muhasebe Konuları Buraya Kaydı)
    "Finansal Muhasebe": [
        {"soru": "Varlık ve Kaynakların gösterildiği finansal tablo hangisidir?", "secenekler": ["Bilanço", "Gelir Tablosu", "Mizan"], "cevap": "Bilanço"},
        {"soru": "Tek Düzen Hesap Planında '100 Kasa' hesabı hangi gruptadır?", "secenekler": ["Dönen Varlıklar", "Duran Varlıklar", "Özkaynaklar"], "cevap": "Dönen Varlıklar"},
        {"soru": "Yevmiye defterinden Büyük deftere (Defter-i Kebir) aktarım yapılırken ne kullanılır?", "secenekler": ["Yevmiye Madde Numarası", "Tarih", "Tutar"], "cevap": "Yevmiye Madde Numarası"},
        {"soru": "Borç ve Alacak toplamlarının eşitliğini kontrol eden tablo nedir?", "secenekler": ["Mizan", "Bilanço", "Envanter"], "cevap": "Mizan"},
        {"soru": "Satıcıya veresiye borçlandığımızda hangi hesap çalışır?", "secenekler": ["320 Satıcılar", "120 Alıcılar", "100 Kasa"], "cevap": "320 Satıcılar"},
        {"soru": "Banka hesabına para yatırıldığında '102 Bankalar' hesabı nasıl çalışır?", "secenekler": ["Borçlanır", "Alacaklanır", "Kapanır"], "cevap": "Borçlanır"},
        {"soru": "Dönem net karı veya zararı hangi tabloda sonucunu gösterir?", "secenekler": ["Gelir Tablosu", "Mizan", "Kasa Defteri"], "cevap": "Gelir Tablosu"}
    ],

    # GENEL YEDEK (Her ders için acil durum)
    "Genel": [
        {"soru": "Bir işletmenin en likit varlığı hangisidir?", "secenekler": ["Kasa", "Demirbaş", "Bina"], "cevap": "Kasa"},
        {"soru": "KDV'nin açılımı nedir?", "secenekler": ["Katma Değer Vergisi", "Kurumlar Vergisi", "Gelir Vergisi"], "cevap": "Katma Değer Vergisi"},
        {"soru": "Bilgisayarda 'Kopyala' kısayolu nedir?", "secenekler": ["CTRL+C", "CTRL+V", "CTRL+X"], "cevap": "CTRL+C"},
        {"soru": "Excel'de formül hangi işaretle başlar?", "secenekler": ["=", "?", "%"], "cevap": "="},
        {"soru": "Brüt ücretten kesintiler çıkınca ne kalır?", "secenekler": ["Net Ücret", "Vergi", "Sigorta"], "cevap": "Net Ücret"}
    ]
}

# --- AI AYARLARI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def yapay_zeka_soru_uret(sinif, ders):
    ai_sorulari = []
    
    # 1. KONUYA ÖZEL PROMPT AYARLAMA (Müfredat Kontrolü)
    konu_detayi = ""
    if ders == "Temel Muhasebe" and "9" in sinif:
        konu_detayi = "Konular: Fatura ve yerine geçen belgeler (İrsaliye, Fiş, Serbest Meslek Makbuzu, Gider Pusulası), İşletme Hesabı Defteri, Serbest Meslek Kazanç Defteri, Vergi Dairesi, SGK, Belediye işlemleri. (Bilanço ve Yevmiye SORMA)."
    elif ders == "Finansal Muhasebe":
        konu_detayi = "Konular: Bilanço Eşitliği, Yevmiye Kayıtları, Büyük Defter, Mizan, Tek Düzen Hesap Planı, Varlık ve Kaynak hesapları."
    elif ders == "Bilgisayarlı Muhasebe (Luca)":
        konu_detayi = "Konular: Luca muhasebe programı menüleri, Fiş girişi, Kısayol tuşları, Şirket açma işlemleri."
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Rolün: Lise Öğretmeni.
        Ders: {ders} (Sınıf: {sinif}).
        {konu_detayi}
        
        GÖREV: Bu ders ve konular için TAM 10 ADET çoktan seçmeli soru hazırla.
        Zorluk seviyesi: Öğrenciyi düşündürecek, ezber bozan sorular olsun.
        
        ÇIKTI JSON FORMATINDA OLMALI:
        [ {{ "soru": "...", "secenekler": ["A", "B", "C"], "cevap": "..." }} ]
        """
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        if text_response.startswith("```"):
            text_response = text_response.split("```")[1]
            if text_response.startswith("json"):
                text_response = text_response[4:]
        ai_sorulari = json.loads(text_response)
    except:
        ai_sorulari = []

    # 2. HATA KORUMASI VE YEDEK TAMAMLAMA
    # Eğer AI çalışmazsa veya eksik soru üretirse:
    if len(ai_sorulari) < 10:
        # Önce o dersin kendi yedeğini dene
        ozel_yedek = YEDEK_DEPO.get(ders, [])
        if not ozel_yedek:
            # O dersin yedeği yoksa "Genel" yedekten çek (Hata vermemek için)
            ozel_yedek = YEDEK_DEPO["Genel"]
            
        eksik_sayi = 10 - len(ai_sorulari)
        # Yedekleri karıştır ve ekle
        eklenecekler = random.choices(ozel_yedek, k=eksik_sayi) # choices: tekrar seçebilir (soru bitmesin diye)
        ai_sorulari.extend(eklenecekler)
    
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

# 1. GİRİŞ EKRANI
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
        with st.status(f"Sorular Hazırlanıyor... ({st.session_state.kimlik['ders']})", expanded=True):
            sorular = yapay_zeka_soru_uret(st.session_state.kimlik['sinif'], st.session_state.kimlik['ders'])
            
            # KESİN KORUMA: Sorular bir şekilde boş gelirse bile listeyi zorla doldur.
            if len(sorular) == 0:
                sorular = YEDEK_DEPO["Genel"]
                
            st.session_state.soru_listesi = sorular
            st.session_state.oturum_basladi = True
            st.session_state.yukleniyor = False
            st.rerun()

# 2. SORU EKRANI
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
            time.sleep(1)
            st.session_state.index += 1
            st.rerun()

# 3. SONUÇ EKRANI
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
