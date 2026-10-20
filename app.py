import streamlit as st
import json

# 1. HAFIZA DOSYASINI OKUMA (Senin yazdığın kod, aynen duruyor)
def make_memory():
    try:
        with open("memory.json", mode="r", encoding="utf-8") as memoryf:
            hafiza = json.load(memoryf)
    except FileNotFoundError:
        hafiza = {}
    return hafiza

# 2. LİSTEYİ OLUŞTURMA (try-except ve with open kalktı, yüklenen dosyayı okuyor)
def plan_event(hafiza, kontenjan, yuklenen_dosya):
    # Dosyayı tarayıcı belleğinden metin olarak çözüp satırlara bölüyoruz
    icerik = yuklenen_dosya.getvalue().decode("utf-8").splitlines()
    
    basvuranlar = []
    i = 1
    
    # [1:] yazarak başlık satırını atlıyoruz
    for line in icerik[1:]:
        line = line.strip()
        if line == "":
            continue
        liste = line.split(",")
        time = liste[0]
        name = liste[1]
        phone = liste[2]
        campus = liste[3]

        if phone not in hafiza: 
            hafiza[phone] = {"name": name, "attendance": 0}

        basvuranlar.append({
            "name": name, 
            "phone": phone, 
            "campus": campus, 
            "attendance": hafiza[phone]["attendance"], 
            "sira": i
        })
        i += 1

    sirali = sorted(basvuranlar, key=lambda x: (x["attendance"], x["sira"]))
    secilenler = sirali[:kontenjan]
    yedek = sirali[kontenjan:]
    return secilenler, yedek

# 3. ETKİNLİĞİ TAMAMLAYIP HAFIZAYA KAYDETME (Senin yazdığın kod, print yerine st.success geldi)
def katilim(secilenler, hafiza):
    for kisi in secilenler: 
        tel = kisi["phone"]
        hafiza[tel]["attendance"] += 1
    with open("memory.json", mode="w", encoding="utf-8") as f: 
        json.dump(hafiza, f, ensure_ascii=False, indent=4)
    st.success("🎉 Attendance is successfully saved")

# Listeyi ekrana basılacak şık bir formata sokar (Sıra en başa gelir ve 1'den başlar)
def tabloya_hazirla(liste):
    tablo = []
    for sira, kisi in enumerate(liste, 1):
        tablo.append({
            "No": sira,
            "Name": kisi["name"],
            "Phone": kisi["phone"],
            "Campus": kisi["campus"],
            "Attendance": kisi["attendance"]
        })
    return tablo

# 4. STREAMLIT ARAYÜZÜ (Terminaldeki main'in yerini alan web ekranı)
st.title("CX EVENT PLANNER")

if "dosya_sayaci" not in st.session_state:
    st.session_state["dosya_sayaci"] = 0

st.markdown("""
<style>
th, td {
    text-align: center !important;
}
</style>
""", unsafe_allow_html=True)

# Kontenjan kutusu
kontenjan = st.number_input("Quota of the event:", min_value=1)

# Dosya yükleme alanı
yuklenen_dosya = st.file_uploader("Upload Google Form CSV or TXT File", type=["csv", "txt"], key=f"yukleyici_{st.session_state['dosya_sayaci']}")

if yuklenen_dosya is not None:
    hafiza = make_memory()
    secilenler, yedek = plan_event(hafiza, kontenjan, yuklenen_dosya)

    # Listeleri ekranda şık tablo olarak gösterelim
    st.subheader("📋 First List")
    st.table(tabloya_hazirla(secilenler))

    st.subheader("⏳ Waiting List")
    st.table(tabloya_hazirla(yedek))

    st.markdown("---")
    st.subheader("⚙️ Cancellations")

    # İptal edenleri seçtirme kutusu (Kullanıcı isimleri tık tık seçer)
    asil_isimler = [k["name"] for k in secilenler]
    iptal_edenler = st.multiselect("Select the students that wont attend the event: ", asil_isimler)

    # İptal edenleri listeden çıkarıyoruz
    guncel_secilenler = [k for k in secilenler if k["name"] not in iptal_edenler]

    # Eğer iptal eden varsa, yerine yedekten kimin geldiğini seçtiriyoruz
    if len(iptal_edenler) > 0:
        yedek_isimler = [k["name"] for k in yedek]
        yeni_girenler = st.multiselect(
            f"Choose the students from the waiting list that will attend instead" , 
            yedek_isimler, 
            max_selections=len(iptal_edenler)
        )
        
        # Seçilen yedekleri asil listeye ekliyoruz
        for y_kisi in yedek:
            if y_kisi["name"] in yeni_girenler and y_kisi not in guncel_secilenler:
                guncel_secilenler.append(y_kisi)

    st.subheader("✅ Final List")
    st.table(tabloya_hazirla(guncel_secilenler))

    # Butona basıldığı an veriler memory.json'a yazılır
    if st.button("Finalize the event and save attendance"):
        katilim(guncel_secilenler, hafiza)
        st.session_state["tamamlandi"] = True

    if st.session_state.get("tamamlandi"):
        if st.button("🔄 Plan a new event (reset the page)"):
            st.session_state["tamamlandi"] = False
            st.session_state["dosya_sayaci"] += 1
            st.rerun()

    # --- YÖNETİCİ GÜVENLİ SIFIRLAMA PANELİ (Sidebar - Sol Menü) ---
with st.sidebar:
    st.header("⚙️ Organizer Settings")

    if st.session_state.get("sifirlandi_mesaji"):
        st.success("🎉 All previous attendance data has been successfully deleted!")
        st.session_state["sifirlandi_mesaji"] = False # Mesajı gösterdikten sonra bayrağı indiriyoruz
    
    # Kapalı kutu: Tıklamadan içi açılmaz
    with st.expander("⚠️ Reset Attendance Memory"):
        st.warning("Warning! This can't be undone, all previous attendance records will be deleted.")
        
        # 1. Güvenlik Kilidi: Checkbox
        sifirlama_onayi = st.checkbox("I authorize the reset of the attendance data")
        
        # 2. Güvenlik Kilidi: Buton
        if st.button("🚨 Reset Attendance Data", type="primary"):
            if sifirlama_onayi:
                # memory.json dosyasını sıfırdan boş bir sözlükle eziyoruz
                with open("memory.json", mode="w", encoding="utf-8") as f:
                    json.dump({}, f, ensure_ascii=False, indent=4)
                st.session_state["sifirlandi_mesaji"] = True
                st.rerun()
            else:
                st.error("Please click authorization")