import streamlit as st
import time

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Okul Finans Oyunu", page_icon="💰")

# --- OYUN VERİLERİ (SORULAR BURAYA EKLENİR) ---
sorular = [
    {
        "soru": "Okul kantininden 50 TL'lik tost aldın. Kasadan para çıkışı oldu. Bu işlem muhasebede nasıl kaydedilir?",
        "secenekler": ["Kasa Hesabı Borçlanır", "Kasa Hesabı Alacaklanır", "Sermaye Artar"],
        "cevap": "Kasa Hesabı Alacaklanır",
        "odul": 100
    },
    {
        "soru": "Öğrenci servis ücreti olarak veliden 1000 TL nakit tahsil edildi. Kasa hesabı nasıl çalışır?",
        "secenekler": ["Kasa Hesabı Borçlanır (+Giriş)", "Kasa Hesabı Alacaklanır (-Çıkış)", "Borç Senetleri Azalır"],
        "cevap": "Kasa Hesabı Borçlanır (+Giriş)",
        "odul": 150
    },
    {
        "soru": "Okulun elektrik faturası (500 TL) bankadan ödendi. Hangi hesap azalır?",
        "secenekler": ["Kasa Hesabı", "Bankalar Hesabı", "Alıcılar Hesabı"],
        "cevap": "Bankalar Hesabı",
        "odul": 200
    }
]

# --- OTURUM (HAFIZA) AYARLARI ---
# Puanı ve soru sırasını hafızada tutmak için
if 'bakiye' not in st.session_state:
    st.session_state.bakiye = 0
if 'siradaki_soru' not in st.session_state:
    st.session_state.siradaki_soru = 0
if 'oyun_bitti' not in st.session_state:
    st.session_state.oyun_bitti = False

# --- ARAYÜZ TASARIMI ---
st.title("🎓 Okul Finans Ligi")
st.write("Doğru cevabı ver, kasa bakiyeni yükselt!")

# Üstteki Bilgi Çubuğu (Skor Tablosu)
col1, col2 = st.columns(2)
col1.metric("💰 Kasa Bakiyesi", f"{st.session_state.bakiye} TL")
col2.metric("📝 Soru", f"{st.session_state.siradaki_soru + 1} / {len(sorular)}")

st.divider() # Çizgi çek

# --- OYUN AKIŞI ---
if not st.session_state.oyun_bitti:
    # Şu anki soruyu çek
    aktif_soru = sorular[st.session_state.siradaki_soru]
    
    st.subheader(f"Soru: {aktif_soru['soru']}")
    
    # Seçenekleri buton olarak göster
    for secenek in aktif_soru["secenekler"]:
        if st.button(secenek, use_container_width=True):
            # Cevap Kontrolü
            if secenek == aktif_soru["cevap"]:
                st.success(f"Tebrikler! Doğru Cevap. Kasaya {aktif_soru['odul']} TL girdi.")
                st.session_state.bakiye += aktif_soru["odul"]
                time.sleep(1.5) # 1.5 saniye bekle
            else:
                st.error("Yanlış Cevap! Bu işlem hatalı oldu.")
                time.sleep(1.5)
            
            # Sonraki soruya geç
            if st.session_state.siradaki_soru + 1 < len(sorular):
                st.session_state.siradaki_soru += 1
                st.rerun() # Sayfayı yenile
            else:
                st.session_state.oyun_bitti = True
                st.rerun()

else:
    # OYUN BİTTİ EKRANI
    st.balloons() # Ekrana balonlar yağdır
    st.success("🎉 TEBRİKLER! OYUNU TAMAMLADINIZ.")
    st.write(f"### Toplam Kasa Mevcudu: {st.session_state.bakiye} TL")
    
    if st.button("Oyunu Yeniden Başlat"):
        st.session_state.bakiye = 0
        st.session_state.siradaki_soru = 0
        st.session_state.oyun_bitti = False
        st.rerun()
