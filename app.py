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
    /* 1. Arka Plan: Ihlamur Yeşili */
    .stApp {
        background-color: #F0F4C3 !important; 
    }
    
    /* 2. Yazı Renkleri */
    h1, h2, h3, h4, h5, h6, p, div, span, label, li, .stMarkdown {
        color: #212121 !important;
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* 3. Butonlar: Sarı Kiremit */
    .stButton>button { 
        width: 100%; 
        border-radius: 12px; 
        min-height: 3.5em; 
        font-weight: 700; 
        background-color: #FF7043 !important; 
        color: #FFFFFF !important; 
        border: 2px solid #D84315 !important; 
        white-space: pre-wrap; 
        padding: 10px;
        transition: transform 0.2s;
    }
    
    .stButton>button:hover { 
        background-color: #FF5722 !important; 
        transform: scale(1.02);
    }
    
    /* 4. Input Alanları */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important; 
        color: #000000 !important; 
        border: 2px solid #FF7043 !important;
    }
    
    /* 5. Soru Kartı */
    .big-font { 
        font-size: 18px !important; 
        font-weight: 600; 
        color: #000000 !important; 
        margin-bottom: 20px; 
        padding: 25px; 
        background-color: #FFFFFF; 
        border-left: 10px solid #FF7043;
        border-radius: 10px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        line-height: 1.6;
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

MESLEK_KONULARI = {
    "9. Sınıf Meslek": "Temel Muhasebe, Mesleki Matematik, Ofis Uygulamaları, Mesleki Gelişim.",
    "10. Sınıf Meslek": "Genel Muhasebe, Temel Hukuk, Ekonomi, Klavye Teknikleri.",
    "11. Sınıf Meslek": "Bilgisayarlı Muhasebe, Maliyet Muhasebesi, Vergi ve Beyannameler, Şirketler Muhasebesi, İş Hukuku.",
    "12. Sınıf Meslek": "Dış Ticaret, Kooperatifçilik, Ahilik Kültürü ve Girişimcilik."
}

TYT_KONULARI = {
    "Türkçe": "Paragrafta Anlam (Uzun), Cümlede Anlam, Ses Bilgisi, Yazım Kuralları, Noktalama.",
    "Matematik": "Yeni Nesil Problemler (Hız, Yaş, Yüzde), Temel Kavramlar, Sayı Basamakları, Fonksiyonlar.",
    "Tarih": "İnkılap Tarihi, Osmanlı Kültür Medeniyet, İlk Türk Devletleri.",
    "Coğrafya": "Harita Bilgisi, İklim, Nüfus, Doğal Afetler.",
}

# YEDEK DEPO (PDF'TEN ÇEKİLEN GERÇEK ÇIKMIŞ SORULAR)
YEDEK_TYT_HAVUZ = {
    "Türkçe": [
        {"soru": "(2018 TYT) Arkeogenetik, insanlığa dair geçmişi moleküler genetik teknikler araştıran bir bilim dalı olarak tanımlanabilir. Bazı temel konular üzerindeki çalışmalar henüz sürmekteyse de hızla ---- bir bilim dalı hâline gelmiştir. Bu parçada boş bırakılan yerlere aşağıdakilerden hangisi sırasıyla getirilmelidir?", "secenekler": ["yoluyla - değişken", "sayesinde - benimsenen", "deneyerek - bilinen", "geliştirerek - sevilen", "kullanarak - gelişen"], "cevap": "kullanarak - gelişen"},
        {"soru": "(2019 TYT) Kimileri robotları insanlığın sonunu getirecek bir tehdit (tehlikeli bir durum) olarak görüyor, kimileri de insanları çalışmaktan kurtaracak (alıkoyacak) bir yardımcı olarak. Suya sabuna dokunmayan (sakıncalı konularla ilgilenmeyen), evcil hayvan benzeri robotlar hâlihazırda (şu anda) satılıyor. Bu robotlar etrafındaki nesnelerin ne olduğunu anlıyor (kavrıyor). Bu parçada numaralanmış sözlerden hangisinin anlamı parantez içinde verilen açıklamayla uyuşmamaktadır?", "secenekler": ["tehdit - tehlikeli bir durum", "kurtaracak - alıkoyacak", "Suya sabuna dokunmayan - sakıncalı konularla ilgilenmeyen", "hâlihazırda - şu anda", "anlıyor - kavrıyor"], "cevap": "kurtaracak - alıkoyacak"},
        {"soru": "(2020 TYT) 'Mutlak olan hiçbir şey yoktur.' fikri yaygın bir mantık hatasıdır çünkü bu önermenin kendisi bile en azından bir mutlağı varsayar. Bu önermenin inanmak, 'Herkes yalan söylüyor.' diyen kişinin doğruyu söylediğine inanmak kadar ---- içerir. Boşluğa ne gelmelidir?", "secenekler": ["sağlamlığına - belirsizlik", "geçerliğine - tutarsızlık", "doğruluğuna - karışıklık", "mantığına - sıradanlık", "yaygınlığına - karşıtlık"], "cevap": "geçerliğine - tutarsızlık"},
        {"soru": "(2021 TYT) Bu roman, okuruna ilk bakışta çok keyfi, çok dağınık görünebilir. Yazar ---- yazmış gibi. Oysa bu dağınık görünüşlü malzeme ---- bir şekilde toplanmış ve yapısal bir bütün meydana getirecek şekilde örülmüş. Boşluklara sırasıyla ne gelmelidir?", "secenekler": ["talep edileni - bilinçli", "aklına geleni - titiz", "akışın getirdiğini - ahenkli", "kendinden bekleneni - tutarlı", "uygun düşeni - aleni"], "cevap": "aklına geleni - titiz"},
        {"soru": "(2022 TYT) Empati başkasının duygularına eşlik etmektir; birlikte ya da aynı şekilde veya bir kişinin diğeri sayesinde hissetmesi, duyması, etkilenmesidir. Bu, kuşkusuz başka bir boyuta taşıyabilir insanı çünkü kısmen de olsa 'ben'in hapishanesinden çıkmayı gerektirir. Altı çizili sözle anlatılmak istenen nedir?", "secenekler": ["Başkalarının duygularını anlama çabasında olmak", "Kendi sınırlarının dışındaki hayatları anlamak", "Farklı bakış açılarına karşı ön yargıları kırmak", "Kendisi dışındaki insanların hayatlarına öykünmek", "Diğerlerinin beklentileri karşısında duyarsızlaşmak"], "cevap": "Kendi sınırlarının dışındaki hayatları anlamak"},
        {"soru": "(2023 TYT) Birine 'Gerçekçi ol!' dediğinizde aslında beklentilerini düşür demek istersiniz çünkü karşınızdaki kişinin, sizin çoktan ---- ya da zaten hiç sahip olmadığınız bu hayatın ---- meydan okuyan hayalleri vardır. Boşluklara ne gelmelidir?", "secenekler": ["yok saydığınız - güzelliklerine", "kabullendiğiniz - durağanlığına", "unuttuğunuz - imkânlarına", "yenildiğiniz - güçlüklerine", "vazgeçtiğiniz - sınırlarına"], "cevap": "vazgeçtiğiniz - sınırlarına"},
        {"soru": "(2024 TYT) 'Yazdıkların kime hitap ediyor?' sorusuna verilmiş net bir cevabım yok. Bir iyelik ekiyle 'okurlarım' demeyi de doğrusu beni hiç okumamış olanlara bir saygısızlık olarak değerlendiriyorum. Ancak yine de boşluğa yazdığımı söyleyemiyorum. Yazar hangisine vurgu yapmaktadır?", "secenekler": ["Eserlerini zihninde tasarladığı bir kitleye yönelik ürettiğine", "Her düzeyde okur kitlesine seslenmeyi öncelediğine", "Seçtiği temalarla okurlarını ayrıştırdığına", "Sahiplendiği okurların duyarlılığını geliştirmeye çalıştığına", "Yazılarıyla bütün okurların beğenisini kazanmayı amaçladığına"], "cevap": "Eserlerini zihninde tasarladığı bir kitleye yönelik ürettiğine"}
    ],
    "Matematik": [
        {"soru": "(2023 TYT Benzeri) Bir manav elindeki elmaların 1/3'ünü %20 karla, kalanını %40 karla satıyor. Toplam kar oranı yüzde kaçtır?", "secenekler": ["%30", "%25", "%33.3", "%35", "%28"], "cevap": "%33.3"},
        {"soru": "(2022 TYT Benzeri) Ardışık 5 çift sayının toplamı 130 ise en küçük sayı kaçtır?", "secenekler": ["22", "20", "24", "26", "18"], "cevap": "22"},
        {"soru": "(2021 TYT Benzeri) A ve B şehirleri arası 600 km'dir. Bir araç 100 km hızla kaç saatte gider?", "secenekler": ["6", "5", "7", "4", "8"], "cevap": "6"},
        {"soru": "(Yeni Nesil) f(x) = 3x - 2 ise f(5) kaçtır?", "secenekler": ["13", "15", "10", "12", "14"], "cevap": "13"},
        {"soru": "(Geometri) Bir dikdörtgenin kısa kenarı 10 cm, uzun kenarı 20 cm ise alanı kaç cm² dir?", "secenekler": ["200", "100", "300", "50", "150"], "cevap": "200"}
    ],
    "Tarih": [
        {"soru": "(2020 TYT Benzeri) Mustafa Kemal'in Samsun'a çıkışı (19 Mayıs 1919) Milli Mücadele açısından neyi ifade eder?", "secenekler": ["Kurtuluş Savaşı'nın fiilen başlaması", "Cumhuriyetin ilanı", "Lozan Antlaşması", "TBMM'nin açılışı", "Saltanatın kaldırılması"], "cevap": "Kurtuluş Savaşı'nın fiilen başlaması"},
        {"soru": "(2019 TYT Benzeri) İlk Türk devletlerinde 'Töre' nedir?", "secenekler": ["Yazısız hukuk kuralları", "Dini kurallar", "Yazılı anayasa", "Hükümdar emirleri", "Askeri kurallar"], "cevap": "Yazısız hukuk kuralları"},
        {"soru": "(2021 TYT Benzeri) Hangi antlaşma ile Osmanlı Devleti fiilen sona ermiştir?", "secenekler": ["Mondros Ateşkes Antlaşması", "Sevr Antlaşması", "Lozan Antlaşması", "Mudanya Ateşkesi", "Paris Antlaşması"], "cevap": "Mondros Ateşkes Antlaşması"},
        {"soru": "(2022 TYT Benzeri) Cumhuriyetçilik ilkesi neyi esas alır?", "secenekler": ["Milli egemenliği", "Dini yönetimi", "Padişahlığı", "Ekonomik bağımsızlığı", "Devletçiliği"], "cevap": "Milli egemenliği"}
    ],
    "Coğrafya": [
        {"soru": "(2021 TYT Benzeri) Türkiye'de doğudan batıya gidildikçe yerel saatin geri gelmesinin temel nedeni nedir?", "secenekler": ["Dünya'nın batıdan doğuya dönmesi", "Dünya'nın şekli", "Eksen eğikliği", "Yörünge hareketi", "Enlem etkisi"], "cevap": "Dünya'nın batıdan doğuya dönmesi"},
        {"soru": "(2023 TYT Benzeri) Aşağıdakilerden hangisi Karadeniz ikliminin özelliğidir?", "secenekler": ["Her mevsim yağışlı olması", "Yazların kurak geçmesi", "Kışların çok soğuk olması", "Bitki örtüsünün maki olması", "Kar yağışının az olması"], "cevap": "Her mevsim yağışlı olması"},
        {"soru": "(2020 TYT Benzeri) Türkiye'de deprem riskinin en az olduğu bölge hangisidir?", "secenekler": ["Konya - Karaman çevresi", "Ege Bölgesi", "Marmara Bölgesi", "Doğu Anadolu", "Karadeniz kıyıları"], "cevap": "Konya - Karaman çevresi"},
        {"soru": "(2022 TYT Benzeri) Nüfus piramitlerinde tabanın geniş olması neyi ifade eder?", "secenekler": ["Doğum oranının yüksek olduğunu", "Yaşlı nüfusun fazla olduğunu", "Gelişmiş ülke olduğunu", "Ölüm oranının az olduğunu", "Eğitim seviyesini"], "cevap": "Doğum oranının yüksek olduğunu"}
    ]
}

# --- FONKSİYONLAR (EN ÜSTTE TANIMLANDI) ---

def reset_app():
    """Uygulamayı sıfırlar ve ana menüye döner."""
    st.session_state.oturum_basladi = False
    st.session_state.soru_listesi = []
    st.session_state.index = 0
    st.session_state.puan = 0
    st.session_state.kayit_ok = False
    st.session_state.yukleniyor = False
    st.rerun()

def cevap_kontrol(secilen, dogru):
    """Cevabı kontrol eder, puanı artırır ve sonraki soruya geçer."""
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
    """Yapay Zeka veya Yedek Depo kullanarak soru üretir."""
    ai_sorulari = []
    
    is_genel_deneme = "Türkiye Geneli" in alt_baslik
    
    if is_genel_deneme:
        soru_sayisi = 40 
        zorluk = "ZOR (ÖSYM AYARI)"
        konu_detayi = "10 Türkçe, 10 Mat, 10 Tarih, 10 Coğ"
    elif "Meslek" in kategori:
        soru_sayisi = 15
        zorluk = "ORTA-ZOR"
        konu_detayi = MESLEK_KONULARI.get(alt_baslik, "Genel Meslek")
    else:
        soru_sayisi = 15
        zorluk = "ZOR"
        konu_detayi = TYT_KONULARI.get(alt_baslik, "Genel TYT")

    # 1. AI ile Soru Üret
    if "GOOGLE_API_KEY" in st.secrets:
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"""
            Rol: Sınav Hazırlama Uzmanı.
            Kategori: {kategori} - {alt_baslik}
            Zorluk: {zorluk}
            Konu: {konu_detayi}
            Adet: {soru_sayisi}
            
            KURALLAR:
            1. Sorular lise öğrencileri için {zorluk} seviyesinde olsun.
            2. Türkçe: UZUN PARAGRAF. Mat: YENİ NESİL. Sosyal: YORUM.
            3. Çıktı SADECE JSON formatında.
            
            JSON FORMATI:
            [ {{ "soru": "Uzun soru metni...", "secenekler": ["A", "B", "C", "D", "E"], "cevap": "Cevap Metni (A/B gibi harf değil!)" }} ]
            """
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```"): text = text.split("```")[1].strip()
            if text.startswith("json"): text = text[4:].strip()
            ai_sorulari = json.loads(text)
        except:
            ai_sorulari = []

    # 2. Yedek Depo ile Tamamla (Eğer AI eksik üretirse)
    if len(ai_sorulari) < soru_sayisi:
        yedek_listesi = []
        if is_genel_deneme:
            for ders, sorular in YEDEK_TYT_HAVUZ.items():
                yedek_listesi.extend(sorular)
        elif "Meslek" in kategori:
            yedek_listesi = YEDEK_TYT_HAVUZ.get("Türkçe", []) # Meslek için varsayılan
        else:
            yedek_listesi = YEDEK_TYT_HAVUZ.get(alt_baslik, [])
        
        # Yedeği karıştır
        random.shuffle(yedek_listesi)
        
        # Yetersizse çoğalt
        eksik = soru_sayisi - len(ai_sorulari)
        while len(yedek_listesi) < eksik:
            yedek_listesi.extend(yedek_listesi)
            
        ai_sorulari.extend(yedek_listesi[:eksik])
            
    # Şıkları önden karıştırıp sabitle
    for soru in ai_sorulari:
        random.shuffle(soru["secenekler"])
        
    return ai_sorulari[:soru_sayisi]

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
        secenekler = ["Türkçe", "Matematik", "Tarih", "Coğrafya"] + [f"Türkiye Geneli Deneme {i}" for i in range(1, 11)]
        etiket = "Ders / Deneme Seçiniz:"
        soru_bilgisi = "Tek Ders: 15 Soru | Genel Deneme: 40 Soru"

    secilen_alt_baslik = st.selectbox(etiket, secenekler)
    st.caption(f"ℹ️ **Format:** {soru_bilgisi}")

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
        with st.status("Yapay Zeka Soruları Hazırlıyor...", expanded=True):
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
    
    # Şıklar zaten karıştırıldı, burada sadece gösteriyoruz.
    secenekler = soru["secenekler"]
    col1, col2 = st.columns(2)
    for i, sec in enumerate(secenekler):
        # Callback (Tıklanınca çalışacak fonksiyon)
        if i < len(secenekler) / 2:
            with col1:
                st.button(sec, key=f"btn_{st.session_state.index}_{i}", use_container_width=True, on_click=cevap_kontrol, args=(sec, soru["cevap"]))
        else:
            with col2:
                st.button(sec, key=f"btn_{st.session_state.index}_{i}", use_container_width=True, on_click=cevap_kontrol, args=(sec, soru["cevap"]))

# SONUÇ EKRANI
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
