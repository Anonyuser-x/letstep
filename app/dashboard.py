import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import requests

# --- 1. Sayfa Yapılandırması ve API Ayarları ---
st.set_page_config(
    page_title="Bireysel Gelişim Paneli",
    page_icon="🧠",
    layout="wide"
)

BASE_API_URL = "http://127.0.0.1:8000"  # API adresiniz


# --- 2. Stil ve Yardımcı Fonksiyonlar (İlk Dosyadan) ---

def st_hata_sinyal_kartlari():
    """Detaylı Hata Analizi altındaki 3 bilgi kartını, belirgin çerçevelerle gösteren fonksiyon."""
    st.markdown("""
        <style>
            .bilgi-karti {
                flex: 1;
                min-width: 250px;
                border-radius: 8px;
                padding: 1.25rem;
                border: 1px solid;
            }
            .bilgi-karti h6 { margin-top: 0; font-weight: 600; font-size: 1rem; }
            .bilgi-karti p { font-size: 0.9rem; }

            /* --- AYDINLIK MOD STİLLERİ --- */
            [data-testid="stAppViewContainer"][theme~="light"] .bilgi-karti {
                background-color: #F3F4F6;
                border-color: #D1D5DB;
            }
            [data-testid="stAppViewContainer"][theme~="light"] .bilgi-karti h6 { color: #1F2937; }
            [data-testid="stAppViewContainer"][theme~="light"] .bilgi-karti p { color: #4B5563; }

            /* --- KARANLIK MOD STİLLERİ --- */
            [data-testid="stAppViewContainer"][theme~="dark"] .bilgi-karti {
                background-color: #262730;
                border-color: #6B7280;
            }
            [data-testid="stAppViewContainer"][theme~="dark"] .bilgi-karti h6 { color: #FFFFFF; }
            [data-testid="stAppViewContainer"][theme~="dark"] .bilgi-karti p { color: #BDC3C7; }
        </style>
        <div style="display:flex; flex-wrap: wrap; gap: 15px; margin-top: 20px;">
            <div class="bilgi-karti">
                <h6>⚡ Aceleci Hata</h6>
                <p>Ortalamadan çok daha hızlı verilen cevapları gösterir. Genellikle dikkatsizlik veya soruyu tam okumamaktan kaynaklanır.</p>
            </div>
            <div class="bilgi-karti">
                <h6>🧠 Kavramsal Zorluk</h6>
                <p>Ortalamadan çok daha yavaş verilen cevapları gösterir. Öğrencinin konuyu anlamak için yoğun çaba sarf ettiğini ama zorlandığını işaret eder.</p>
            </div>
            <div class="bilgi-karti">
                <h6>🔁 Takılma Noktası</h6>
                <p>Aynı soruya defalarca yanlış cevap verildiğini gösterir. Bu, öğrencinin o spesifik soruda veya konseptte 'takılıp kaldığını' belirtir.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)


def display_chart_without_toolbar(fig: go.Figure):
    """Verilen bir Plotly figürünü, üzerinde araç çubuğu olmadan Streamlit'te gösterir."""
    config = {'displayModeBar': False}
    st.plotly_chart(fig, use_container_width=True, config=config)


def get_recommendation(row):
    """Her bir hata satırı için dinamik bir öneri metni oluşturur."""
    hata_tipi = row.get('Hata_Tipi_kod')
    if hata_tipi == 'kelime':
        return f"'{row['Doğru Cevap']}' kelimesini heceleyerek ve cümle içinde kullanarak pratik yapın."
    elif hata_tipi == 'harf':
        return f"'{row['Doğru Cevap']}' ve '{row['Öğrencinin Cevabı']}' harflerini içeren kelime avı oyunu oynayın."
    elif hata_tipi == 'anlam':
        return f"'{row['Doğru Cevap']}' kelimesinin zıt ve eş anlamlılarını bularak anlamını pekiştirin."
    else:
        return "Bu konuyu tekrar etmek faydalı olacaktır."


# --- 3. Veri Yükleme ve İşleme (İkinci Dosyadan Entegre Edildi) ---

@st.cache_data(ttl=600)
def load_data_from_api(user_id, headers):
    """Belirtilen kullanıcı ID'si için FastAPI endpoint'lerinden YETKİLİ isteklerle veri yükler."""
    if not user_id or not headers:
        return None, None

    activity_url = f"{BASE_API_URL}/dashboard/{user_id}/activity-data"
    try:
        response_activity = requests.get(activity_url, headers=headers, timeout=10)
        response_activity.raise_for_status()
        activity_json = response_activity.json()
        df_activity = pd.read_json(activity_json, orient='split')
    except requests.exceptions.HTTPError as e:
        # Hata yönetimi ana `try-except` bloğunda yapılacağı için burada None döndürüyoruz.
        raise e
    except requests.exceptions.RequestException as e:
        raise e

    # Egzersiz özet verisini çekme (henüz kullanılmıyor ama altyapı hazır)
    exercise_url = f"{BASE_API_URL}/dashboard/{user_id}/exercise-summary"
    df_exercise_summary = pd.DataFrame()
    try:
        response_exercise = requests.get(exercise_url, headers=headers, timeout=10)
        response_exercise.raise_for_status()
        exercise_json = response_exercise.json()
        df_exercise_summary = pd.read_json(exercise_json, orient='split')
    except requests.exceptions.RequestException:
        st.toast(f"Bilgi: Bu öğrenci için ek egzersiz özet verisi bulunamadı.", icon="ℹ️")

    df = df_activity.copy()
    if df.empty:
        return df, df_exercise_summary

    # --- Veri Ön İşleme (İlk dosyadan alındı ve API verisine uyarlandı) ---
    df['datetime'] = pd.to_datetime(df['datetime'])

    kategori_map = {'word': 'Kelime', 'letter': 'Harf', 'direction': 'Yön',
                    'spelling': 'Heceleme', 'meaning': 'Anlam Bilgisi'}
    df['Kategori'] = df['Kategori_kod'].map(kategori_map)

    if not df.empty:
        df = df.sort_values('datetime')
        df['Eğitim Haftası'] = df.groupby('user_id')['datetime'].transform(
            lambda x: (x - x.min()).dt.days // 7 + 1
        )
        df['Hafta Etiketi'] = "Hafta " + df['Eğitim Haftası'].astype(str)

    gun_map_tr = {'Monday': 'Pazartesi', 'Tuesday': 'Salı', 'Wednesday': 'Çarşamba', 'Thursday': 'Perşembe',
                  'Friday': 'Cuma', 'Saturday': 'Cumartesi', 'Sunday': 'Pazar'}

    # API'den gelen 'day_of_week' sütununu kullan, yoksa hesapla
    if 'day_of_week' in df.columns and pd.api.types.is_string_dtype(df['day_of_week']):
        df['Haftanın Günü'] = df['day_of_week']
    else:
        df['Haftanın Günü'] = df['datetime'].dt.day_name().map(gun_map_tr)

    def get_time_of_day(hour):
        if 5 <= hour < 12:
            return 'Sabah (05-12)'
        elif 12 <= hour < 18:
            return 'Öğlen (12-18)'
        elif 18 <= hour < 22:
            return 'Akşam (18-22)'
        else:
            return 'Gece (22-05)'

    df['Günün Zamanı'] = df['datetime'].dt.hour.apply(get_time_of_day)

    if not df.empty:
        df['Öneri'] = df.apply(get_recommendation, axis=1)

    return df, df_exercise_summary


# --- 4. Ana Uygulama Mantığı ---

# URL'den parametreleri al
query_params = st.query_params
student_id_from_url = query_params.get("student_id")
token_from_url = query_params.get("token")

if not student_id_from_url or not token_from_url:
    st.title("Bireysel Gelişim Paneline Hoş Geldiniz")
    st.error("❌ Hata: Raporu görüntülemek için gerekli olan 'Öğrenci ID' veya 'Yetki Token' bilgisi eksik.")
    st.info("Lütfen bu sayfaya Öğretmen Panelindeki 'Raporu Gör' butonuna tıklayarak gelin.")
    st.stop()

try:
    STUDENT_ID = int(student_id_from_url)
    auth_headers = {"Authorization": f"Bearer {token_from_url}"}

    student_df_base, student_exercise_summary = load_data_from_api(STUDENT_ID, headers=auth_headers)

    if student_df_base is None:  # Fonksiyonda kritik bir hata oluştu
        st.stop()

    if student_df_base.empty:
        st.title(f"Öğrenci Paneli: ID {STUDENT_ID}")
        st.info(
            f"📚 {STUDENT_ID} numaralı öğrenci için henüz analiz edilecek bir aktivite (hata) kaydı bulunmamaktadır.")
        st.stop()

    # --- BURADAN SONRASI İLK DOSYANIN ARAYÜZÜNÜN BAŞLANGICI ---
    st.title(f"Bireysel Gelişim Paneli: Öğrenci {STUDENT_ID}")
    st.write(f"Öğrenci {STUDENT_ID} için temel beceri alanlarındaki gelişim alanları ve öneriler.")
    st.markdown("---")

    tab1, tab2 = st.tabs(["📊 Genel Bakış", "📈 Egzersiz Bazında Haftalık Gelişim"])

    with tab1:
        st.header("Genel Performans Analizi (Tüm Zamanlar)")

        with st.expander("🎯 Hangi Egzersizlere Odaklanmalıyız? (Genel Hata Dağılımı)", expanded=False):
            if student_df_base.empty or 'Oyun Tipi' not in student_df_base.columns:
                st.warning("Analiz için yeterli veri bulunamadı.")
            else:
                hata_sayilari = student_df_base['Oyun Tipi'].value_counts().reset_index()
                hata_sayilari.columns = ['Oyun Tipi', 'Hata Sayısı']
                toplam_hata = student_df_base.shape[0]

                if toplam_hata > 0:
                    hata_sayilari['Hata Yüzdesi'] = (hata_sayilari['Hata Sayısı'] / toplam_hata) * 100
                else:
                    hata_sayilari['Hata Yüzdesi'] = 0

                hata_sayilari = hata_sayilari.sort_values('Hata Yüzdesi', ascending=False).reset_index(drop=True)
                hata_sayilari['Sıralama'] = hata_sayilari.index + 1
                hata_sayilari['100de_hata_sayisi'] = hata_sayilari['Hata Yüzdesi'].round().astype(int)
                hata_sayilari_sorted_asc = hata_sayilari.sort_values('Hata Yüzdesi', ascending=True)

                fig_game = go.Figure(go.Bar(
                    y=hata_sayilari_sorted_asc['Oyun Tipi'],
                    x=hata_sayilari_sorted_asc['Hata Yüzdesi'],
                    orientation='h',
                    customdata=hata_sayilari_sorted_asc[['100de_hata_sayisi', 'Sıralama']],
                    marker=dict(color=hata_sayilari_sorted_asc['Hata Yüzdesi'], colorscale='Blues', showscale=False),
                    hovertemplate=(
                        "<b>%{y}</b><br><br>"
                        "Tüm Hatalardaki Pay: <b>%{x:.1f}%</b><br><br>"
                        "ⓘ Bu, yapılan her 100 hatanın yaklaşık <b>%{customdata[0]}</b> tanesinin bu egzersizden geldiği anlamına gelir.<br>"
                        "🏆 Aynı zamanda bu, en sık hata yapılan <b>%{customdata[1]}. egzersiz türüdür.</b>"
                        "<extra></extra>"
                    )
                ))
                fig_game.update_layout(
                    title_text="Hataların Egzersiz Türlerine Göre Dağılımı",
                    template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    xaxis_title="Tüm Hatalar İçindeki Yüzdesel Pay (%)", yaxis_title=None, font_color="#FFFFFF"
                )

                # Değişiklik burada: Orijinal st.plotly_chart yerine yeni fonksiyonu kullanıyoruz.
                display_chart_without_toolbar(fig_game)

                if not hata_sayilari.empty:
                    en_yuksek_hatali_egzersiz = hata_sayilari.iloc[0]
                    en_yuksek_hatali_egzersiz_adi = en_yuksek_hatali_egzersiz['Oyun Tipi']
                    en_yuksek_hata_yuzdesi = en_yuksek_hatali_egzersiz['Hata Yüzdesi']
                    oneri_sozlugu = {
                        'anlam seçme': "Kısa hikayeler veya metinler okuyup, 'Bu metin ne anlatıyor?' sorusunu sormak, anlama ve yorumlama becerilerini güçlendirir.",
                        'kelime seslerinde uyum': "Benzer sesli ama farklı anlamlı kelimelerle (örn: kar-kâr) küçük oyunlar oynamak veya tekerlemeler söylemek faydalı olabilir.",
                        'ilk harfi yakalama': "Nesnelerin veya resimlerin baş harfini bulma oyunu oynamak, hem eğlenceli hem de öğreticidir.",
                        'karmaşık harflerden kelime oluştur': "Buzdolabına manyetik harfler yapıştırarak her gün yeni bir kelime oluşturmasını istemek, bu beceriyi pratik hale getirir.",
                        'yön takibi': "Günlük hayatta 'Sağındaki oyuncağı ver' veya 'Solundaki kapıya git' gibi somut komutlarla yön kavramlarını pekiştirebilirsiniz.",
                        'boşluklara doğru harfi koy': "Eksik harfli kelime tamamlama bulmacaları veya kelime tombalası oynamak, harf bilgisini güçlendirir.",
                        'akıl yürütme': "Basit mantık bulmacaları çözmek veya bir olayın 'neden' ve 'sonucunu' tartışmak, akıl yürütme becerisini geliştirir.",
                        'anlam bağdaştırma': "İki farklı nesne veya kavram arasında 'Ne gibi ortak yönleri var?' diye sormak, bağdaştırma yeteneğini artırır.",
                        'boşluğu doldur': "Cümle tamamlama etkinlikleri yapmak veya bir hikayenin sonunu onun getirmesini istemek, bu alanda ona yardımcı olur.",
                        'harf karıştırma': "Karışık harflerden anlamlı kelimeler türetme (anagram) oyunları, harf sıralama becerisini keskinleştirir.",
                        'hecelere ayırma': "Kelimeyi hecelerine ayırırken alkış tutmak gibi ritmik ve eğlenceli aktiviteler, heceleme becerisini kalıcı hale getirir.",
                        'nesne yönü tanıma': "Evdeki nesneleri kullanarak 'Masanın üzerindeki top nerede?' gibi sorularla konum ve yön bilgisini pekiştirebilirsiniz."
                    }
                    ozel_oneri = oneri_sozlugu.get(en_yuksek_hatali_egzersiz_adi.lower().strip(),
                                                   "Bu konunun temellerini tekrar gözden geçirmek önemlidir.")
                    # ESKİ st.markdown BLOĞUNU SİLİP, YERİNE AYNEN BUNU YAPIŞTIR:

                    st.markdown(f"""
                            <style>
                                /* Bu kutuya özel bir ID tanımlayalım ki diğer elementleri etkilemesin */
                                #analiz-raporu-karti {{
                                    border-radius: 8px;
                                    padding: 1.5rem;
                                    border: 1px solid;
                                    margin-bottom: 1rem;
                                }}
                                #analiz-raporu-karti h5 {{
                                    margin-top: 0;
                                    font-weight: bold;
                                }}
                                #analiz-raporu-karti hr {{
                                    margin: 1.5rem 0;
                                    border-style: solid;
                                    opacity: 0.5;
                                }}
                                #analiz-raporu-karti ol {{
                                    padding-left: 1.2rem;
                                }}
                                #analiz-raporu-karti li {{
                                    margin-bottom: 0.5rem;
                                }}

                                /* --- AYDINLIK MOD (LIGHT MODE) İÇİN RENKLER --- */
                                [data-testid="stAppViewContainer"][theme~="light"] #analiz-raporu-karti {{
                                    background-color: #FFFFFF;  /* Temiz beyaz arka plan */
                                    border-color: #E5E7EB;      /* Çok hafif gri kenarlık */
                                }}
                                [data-testid="stAppViewContainer"][theme~="light"] #analiz-raporu-karti h5 {{
                                    color: #111827; /* Neredeyse siyah, güçlü başlık */
                                }}
                                [data-testid="stAppViewContainer"][theme~="light"] #analiz-raporu-karti p,
                                [data-testid="stAppViewContainer"][theme~="light"] #analiz-raporu-karti li {{
                                    color: #374151; /* Çok okunaklı koyu gri metin */
                                }}
                                [data-testid="stAppViewContainer"][theme~="light"] #analiz-raporu-karti hr {{
                                    border-color: #E5E7EB; /* Hafif ayırıcı çizgi */
                                }}

                                /* --- KARANLIK MOD (DARK MODE) İÇİN RENKLER (SİZİN GÖRSELDEKİ GİBİ) --- */
                                [data-testid="stAppViewContainer"][theme~="dark"] #analiz-raporu-karti {{
                                    background-color: #262730; /* Sizin istediğiniz arka plan */
                                    border-color: #333;         /* Sizin istediğiniz kenarlık */
                                }}
                                [data-testid="stAppViewContainer"][theme~="dark"] #analiz-raporu-karti h5 {{
                                    color: #A9CCE3; /* Sizin istediğiniz başlık rengi */
                                }}
                                [data-testid="stAppViewContainer"][theme~="dark"] #analiz-raporu-karti p,
                                [data-testid="stAppViewContainer"][theme~="dark"] #analiz-raporu-karti li {{
                                    color: #BDC3C7; /* Sizin istediğiniz metin rengi */
                                }}
                                [data-testid="stAppViewContainer"][theme~="dark"] #analiz-raporu-karti hr {{
                                    border-color: #333; /* Sizin istediğiniz ayırıcı çizgi */
                                }}
                            </style>

                            <!-- HTML yapısı aynı, sadece en dıştaki div'e bir ID ekledik -->
                            <div id="analiz-raporu-karti">
                                <h5>Analiz Raporu</h5>
                                <p>
                                Grafiğe göre, yapılan tüm hataların <b>%{en_yuksek_hata_yuzdesi:.1f}</b>'i gibi önemli bir kısmı <b>'{en_yuksek_hatali_egzersiz_adi}'</b> egzersiz türünde yoğunlaşmış durumda. Bu, şu an en çok destek gerektiren alanın burası olduğunu gösteriyor.
                                </p>
                                <hr>
                                <h5>Ne Yapabilirsiniz?</h5>
                                <ol>
                                    <li><b>Öncelik Belirleyin:</b> Öncelikle <b>'{en_yuksek_hatali_egzersiz_adi}'</b> egzersizine odaklanın. Bu alandaki pratikleri artırmak en verimli sonucu verecektir.</li>
                                    <li><b>Birlikte Çalışın:</b> {ozel_oneri}</li>
                                    <li><b>Gelişimi Kutlayın:</b> Çabasını takdir edin ve bir süre sonra bu grafiğe dönerek hata oranındaki düşüşü birlikte gözlemleyin.</li>
                                </ol>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("Tebrikler! Analiz edilecek herhangi bir hata bulunamadı.")

        # --- DEĞİŞİKLİK BURADA: EKSİK BÖLÜM GERİ EKLENDİ ---
        with st.expander("📊 İkili Analiz: Hata Yoğunluğu & Israr Seviyesi", expanded=False):
            df_analysis = student_df_base.groupby('Oyun Tipi').agg(
                Toplam_Hata_Sayısı=('Oyun Tipi', 'size'),
                Toplam_Tekrar_Sayısı=('Tekrar Sayısı', 'sum')
            ).reset_index()

            if not df_analysis.empty:
                toplam_hata_genel = df_analysis['Toplam_Hata_Sayısı'].sum()
                df_analysis['Hata Yoğunluğu (%)'] = (df_analysis['Toplam_Hata_Sayısı'] / toplam_hata_genel) * 100
                df_analysis['Israr Seviyesi'] = df_analysis.apply(
                    lambda row: row['Toplam_Tekrar_Sayısı'] / row['Toplam_Hata_Sayısı'] if row[
                                                                                               'Toplam_Hata_Sayısı'] > 0 else 0,
                    axis=1
                )
                df_analysis_sorted = df_analysis.sort_values('Hata Yoğunluğu (%)', ascending=False)
                col1, col2 = st.columns(2)
                with col1:
                    fig_yogunluk = px.bar(
                        df_analysis_sorted, x='Oyun Tipi', y='Hata Yoğunluğu (%)',
                        title="Hata Yoğunluğu: En Sık Hata Yapılanlar", template="plotly_dark",
                        color_discrete_sequence=['#636EFA']
                    )
                    fig_yogunluk.update_traces(
                        hovertemplate="<b>%{x}</b><br>Hata Yoğunluğu: %{y:.1f}%<br><extra>Anlamı: Her 100 hatanın yaklaşık %{y:.0f} tanesi bu egzersizdendir.</extra>")
                    fig_yogunluk.update_layout(xaxis_title=None, yaxis_title="Hatalar İçindeki Pay (%)",
                                               xaxis={'categoryorder': 'total descending'})

                    # Değişiklik burada: Orijinal st.plotly_chart yerine yeni fonksiyonu kullanıyoruz.
                    display_chart_without_toolbar(fig_yogunluk)
                with col2:
                    fig_israr = px.bar(
                        df_analysis_sorted, x='Oyun Tipi', y='Israr Seviyesi',
                        title="Israr Seviyesi: En Çok Zorlanılanlar", template="plotly_dark",
                        color_discrete_sequence=['#00CC96'],
                        category_orders={'Oyun Tipi': df_analysis_sorted['Oyun Tipi'].tolist()}
                    )
                    fig_israr.update_traces(
                        hovertemplate="<b>%{x}</b><br>Israr Seviyesi: %{y:.2f} tekrar/hata<br><extra>Anlamı: Bu türde bir hata sonrası ortalama %{y:.2f} kez daha dener.</extra>")
                    fig_israr.update_layout(xaxis_title=None, yaxis_title="Hata Başına Ortalama Tekrar")

                    # Değişiklik burada: Orijinal st.plotly_chart yerine yeni fonksiyonu kullanıyoruz.
                    display_chart_without_toolbar(fig_israr)
                st.markdown("<hr>", unsafe_allow_html=True)
                st.subheader("Bu Grafikler Ne Anlatıyor?")
                st.markdown("""
                    <div style="display:flex; flex-wrap: wrap; gap: 20px; margin-top:10px;">
                        <div style="flex:1; min-width: 300px; border: 1px solid #636EFA; border-radius: 8px; padding: 15px; background-color: rgba(99, 110, 250, 0.1);">
                            <h5 style="color:#636EFA;">Hata Yoğunluğu Grafiği (Mavi)</h5>
                            <p>Bu grafik, <b>"Ne kadar sık?"</b> sorusunu cevaplar. Uzun çubuklar, çocuğunuzun en çok hangi egzersiz türlerinde hata yaptığını gösterir. Bu, genel pratik eksikliğine veya dikkatsizliğe işaret edebilir.</p>
                        </div>
                        <div style="flex:1; min-width: 300px; border: 1px solid #00CC96; border-radius: 8px; padding: 15px; background-color: rgba(0, 204, 150, 0.1);">
                            <h5 style="color:#00CC96;">Israr Seviyesi Grafiği (Yeşil)</h5>
                            <p>Bu grafik, <b>"Ne kadar zor?"</b> sorusunu cevaplar. Uzun çubuklar, çocuğunuzun bir hata yaptıktan sonra en çok hangi egzersizlerde "takılıp kaldığını" gösterir. Bu, genellikle konunun temel mantığını anlamakta zorlandığının bir işaretidir.</p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown("<hr>", unsafe_allow_html=True)
                st.subheader("Analiz Raporu ve Öneriler")
                en_yogun_hata_alani = df_analysis_sorted.iloc[0]['Oyun Tipi']
                en_yuksek_israr_alani = df_analysis.sort_values('Israr Seviyesi', ascending=False).iloc[0]['Oyun Tipi']
                col_rapor1, col_rapor2 = st.columns(2)
                col_rapor1.metric("En Sık Hata Yapılan Alan", en_yogun_hata_alani)
                col_rapor2.metric("En Çok Zorlanılan Alan", en_yuksek_israr_alani)
                st.markdown("##### Ne Yapabilirsiniz?")
                if en_yogun_hata_alani == en_yuksek_israr_alani:
                    st.error(
                        f"**DİKKAT: '{en_yogun_hata_alani}' şu an en öncelikli konu.** Çocuğunuz bu konuda hem çok sık hata yapıyor hem de bu hatalarda çok zorlanıyor. Bu konunun temeline inerek, farklı ve eğlenceli yöntemlerle pratik yapmak en doğru yaklaşım olacaktır.")
                else:
                    st.info(
                        f"**İki Farklı Duruma Odaklanılmalı:**\n\n1. **'{en_yogun_hata_alani}'** egzersizindeki hatalar sık yaşanıyor. Bu konudaki pratikleri artırarak ve dikkatini toplamasına yardımcı olarak bu yoğunluğu azaltabilirsiniz.\n2. **'{en_yuksek_israr_alani}'** egzersizinde ise konunun mantığını anlamakta güçlük çekiyor olabilir. Bu egzersizi birlikte açıp düşünce tarzını anlamaya çalışmak ve konuyu farklı bir yolla anlatmak, 'takılıp kalmasını' önleyecektir.")
            else:
                st.success("Analiz edilecek yeterli hata verisi bulunmamaktadır.")


        # MEVCUT with st.expander(...) BLOĞUNU SİLİP, YERİNE BUNU YAPIŞTIR

        # Callback fonksiyonu burada kalıyor, bu doğru.
        def temizle_filtre():
            st.session_state.selected_games_filter = []


        # MEVCUT with st.expander(...) BLOĞUNU SİLİP, YERİNE BUNU YAPIŞTIR

        # Callback fonksiyonu burada kalıyor, bu doğru.
        def temizle_filtre():
            st.session_state.selected_games_filter = []
            # İşaretçiyi de temizleyelim
            if 'form_submitted' in st.session_state:
                del st.session_state.form_submitted


        # --- DEĞİŞİKLİK 1: expander'ı session_state'e bağla ---
        # Form gönderildiyse 'expanded' True olacak, değilse False.
        with st.expander("🧠 Bilge Danışman: Hataların Dili ve Akıllı Öneriler",
                         expanded=st.session_state.get('form_submitted', False)):

            st.markdown("##### Egzersize Göre Filtrele")
            error_analysis_df = student_df_base[
                ['Oyun Tipi', 'Yanıt Süresi (sn)', 'Tekrar Sayısı', 'Öğrencinin Cevabı', 'Doğru Cevap',
                 'Kategori_kod']].copy()
            unique_game_types = sorted(error_analysis_df['Oyun Tipi'].unique().tolist())

            with st.form(key='bilge_danisman_form'):
                if 'selected_games_filter' not in st.session_state:
                    st.session_state.selected_games_filter = []

                selected_games = st.multiselect(
                    label="Aşağıdaki listeden bir veya daha fazla egzersiz türü seçerek hataları filtreleyebilirsiniz:",
                    options=unique_game_types,
                    key='selected_games_filter',
                    placeholder="Filtrelemek için egzersiz seçin..."
                )

                col1, col2 = st.columns(2)
                with col1:
                    # --- DEĞİŞİKLİK 2: Butona tıklandığında bir işaret bırak ---
                    submit_button = st.form_submit_button(
                        label='Analizi Uygula',
                        use_container_width=True,
                        on_click=lambda: st.session_state.update(form_submitted=True)  # İşareti True yap
                    )
                with col2:
                    clear_button = st.form_submit_button(
                        'Seçimi Temizle',
                        use_container_width=True,
                        on_click=temizle_filtre
                    )

            # --- GERİ KALAN HER ŞEY TAMAMEN AYNI, HİÇBİR DEĞİŞİKLİK YOK ---
            if st.session_state.selected_games_filter:
                filtered_df = error_analysis_df[
                    error_analysis_df['Oyun Tipi'].isin(st.session_state.selected_games_filter)].copy()
            else:
                filtered_df = pd.DataFrame(columns=error_analysis_df.columns)

            st.markdown("---")
            st.markdown("##### Detaylı Hata Analizi")

            if not filtered_df.empty:
                avg_reaction_times = error_analysis_df.groupby('Oyun Tipi')['Yanıt Süresi (sn)'].transform('mean')


                def get_learning_signal(row):
                    avg_time = avg_reaction_times.loc[row.name]
                    reaction_time = row['Yanıt Süresi (sn)']
                    repeat_count = row['Tekrar Sayısı']
                    if repeat_count > 2: return "🔁 Takılma Noktası"
                    if reaction_time < avg_time * 0.5: return "⚡ Aceleci Hata"
                    if reaction_time > avg_time * 1.5: return "🧠 Kavramsal Zorluk"
                    return "–"


                def get_dynamic_suggestion(row):
                    signal = row['Öğrenme Sinyali']
                    category = row['Kategori_kod']
                    if category in ['letter', 'spelling']:
                        base_suggestion = "harflerin yazılışı ve okunuşu üzerine pratik yapmak."
                    elif category in ['word', 'meaning']:
                        base_suggestion = "kelime dağarcığını ve okuduğunu anlama becerilerini geliştirmek."
                    elif category == 'direction':
                        base_suggestion = "yön kavramları (sağ, sol vb.) üzerine somut nesnelerle çalışmak."
                    else:
                        base_suggestion = "bu konunun temellerini tekrar gözden geçirmek."
                    if signal == "⚡ Aceleci Hata":
                        return "Bu hata muhtemelen dikkatsizlikten kaynaklanıyor. 'Soruyu dikkatle okumak' ve 'acele etmemek' üzerine konuşmak daha faydalı olacaktır."
                    elif signal == "🧠 Kavramsal Zorluk":
                        return f"Bu konuda temel bir zorluk yaşanıyor gibi görünüyor. Özellikle, {base_suggestion}"
                    elif signal == "🔁 Takılma Noktası":
                        return f"Bu soruda özel olarak takılıp kalmış. Benzer ama daha kolay bir örnek çözdükten sonra bu soruya dönmek ve {base_suggestion}"
                    else:
                        return f"Bu hatayı çözmek için {base_suggestion.capitalize()}"


                filtered_df['Öğrenme Sinyali'] = filtered_df.apply(get_learning_signal, axis=1)
                filtered_df['Öneri'] = filtered_df.apply(get_dynamic_suggestion, axis=1)

                display_df = filtered_df[['Öğrencinin Cevabı', 'Doğru Cevap', 'Öğrenme Sinyali', 'Öneri']]
                st.table(display_df)

                st_hata_sinyal_kartlari()

            elif not st.session_state.selected_games_filter:
                st.info("Lütfen yukarıdaki listeden bir veya daha fazla egzersiz seçerek analizi başlatın.")
            else:
                st.warning("Seçilen filtrelere uygun hata kaydı bulunamadı.")

        # 4. BÖLÜM: Genel Gelişim Trendi
        with st.expander("⚡ Genel Gelişim Trendi: Düşünme Hızı Zamanla Değişiyor mu?", expanded=False):

            # --- BÖLÜM 1: ARAYÜZ (UI) VE İNTERAKTİF FİLTRELER ---

            # Filtre seçeneklerini session_state'de sakla
            if 'trend_level' not in st.session_state:
                st.session_state.trend_level = "Genel Trend"
            if 'trend_period' not in st.session_state:
                st.session_state.trend_period = "Haftalık"

            st.markdown("##### Analiz Filtreleri")
            col1, col2 = st.columns(2)

            # 1.1. Zorluk Seviyesi Filtresi
            with col1:
                level = st.radio(
                    "Zorluk Seviyesi:",
                    ["Genel Trend", "Ortaokul Soruları", "İlkokul Soruları"],
                    key='trend_level',
                    horizontal=True
                )

            # 1.2. Zaman Periyodu Filtresi
            with col2:
                period_map = {"Günlük": "D", "Haftalık": "W", "Aylık": "M", "2 Aylık": "2ME"}
                period = st.radio(
                    "Zaman Periyodu:",
                    list(period_map.keys()),
                    key='trend_period',
                    horizontal=True
                )

            # --- BÖLÜM 2: ARKA PLAN MANTIĞI (HESAPLAMA VE FİLTRELEME) ---

            df_trend_copy = student_df_base.copy()  # Orijinal veriyi bozmamak için kopya al

            if level == "Ortaokul Soruları":
                df_filtered_trend = df_trend_copy[df_trend_copy['student_profile'] == 'ortaokul']
            elif level == "İlkokul Soruları":
                df_filtered_trend = df_trend_copy[df_trend_copy['student_profile'] == 'ilkokul']
            else:  # "Genel Trend"
                df_filtered_trend = df_trend_copy

            # Tarih sütununu index yapmadan önce varlığından emin ol
            if 'datetime' in df_filtered_trend.columns:
                df_filtered_trend = df_filtered_trend.set_index('datetime')

            if not df_filtered_trend.empty:
                df_resampled = df_filtered_trend['Yanıt Süresi (sn)'].resample(
                    period_map[period]).mean().dropna().reset_index()
                df_resampled.rename(columns={'datetime': 'Tarih', 'Yanıt Süresi (sn)': 'Ortalama Yanıt Süresi'},
                                    inplace=True)
            else:
                df_resampled = pd.DataFrame(columns=['Tarih', 'Ortalama Yanıt Süresi'])

            # --- GRAFİĞİ ÇİZDİRME ---
            grafik_basligi = f"{period} Ortalama Yanıt Süresi ({level.replace(' Soruları', '')})"

            fig_line = px.line(df_resampled, x='Tarih', y='Ortalama Yanıt Süresi', markers=True,
                               title=grafik_basligi, template='plotly_dark')
            fig_line.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                xaxis_title=f"{period} Periyotlar", yaxis_title="Ortalama Yanıt Süresi (Saniye)"
            )

            # Değişiklik burada: Orijinal st.plotly_chart yerine yeni fonksiyonu kullanıyoruz.
            display_chart_without_toolbar(fig_line)

            # --- BÖLÜM 3: AKILLI ANALİZ VE YORUMLAMA ---
            st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)
            st.subheader("Akıllı Analiz ve Yorumlama")

            # ESKİ st.markdown BLOĞUNU SİLİP, YERİNE AYNEN BUNU YAPIŞTIR:

            st.markdown("""
                <style>
                    /* Bu kutuya özel bir ID tanımlıyoruz ki diğer elementleri etkilemesin */
                    #gelisim-yorumu-karti {
                        border-radius: 8px;
                        padding: 1.25rem; /* Biraz daha ferah bir iç boşluk */
                        border: 1px solid; /* Kenarlık rengini tema belirleyecek */
                        margin-bottom: 1rem; /* Altına biraz boşluk bırakalım */
                    }
                    /* ID'ye sahip kutunun içindeki etiketleri hedef alıyoruz */
                    #gelisim-yorumu-karti h6 {
                        margin-top: 0;
                        font-weight: 600;
                    }
                    #gelisim-yorumu-karti p {
                        font-size: 0.9rem;
                        line-height: 1.6; /* Satır aralığını biraz artıralım */
                    }

                    /* --- AYDINLIK MOD (LIGHT MODE) İÇİN RENKLER --- */
                    [data-testid="stAppViewContainer"][theme~="light"] #gelisim-yorumu-karti {
                        background-color: #EFF6FF; /* Çok açık mavi arka plan */
                        border-color: #BFDBFE;     /* Biraz daha belirgin mavi kenarlık */
                    }
                    [data-testid="stAppViewContainer"][theme~="light"] #gelisim-yorumu-karti h6 {
                        color: #1E40AF; /* Okunabilir, koyu mavi başlık */
                    }
                    [data-testid="stAppViewContainer"][theme~="light"] #gelisim-yorumu-karti p {
                        color: #1D4ED8; /* Okunabilir, canlı mavi metin */
                    }

                    /* --- KARANLIK MOD (DARK MODE) İÇİN RENKLER --- */
                    [data-testid="stAppViewContainer"][theme~="dark"] #gelisim-yorumu-karti {
                        background-color: #1E293B; /* Koyu lacivert/gri arka plan */
                        border-color: #2563EB;     /* Belirgin, canlı mavi kenarlık */
                    }
                    [data-testid="stAppViewContainer"][theme~="dark"] #gelisim-yorumu-karti h6 {
                        color: #93C5FD; /* Açık, parlak mavi başlık */
                    }
                    [data-testid="stAppViewContainer"][theme~="dark"] #gelisim-yorumu-karti p {
                        color: #BFDBFE; /* Okunabilir, açık mavi metin */
                    }
                </style>

                <!-- HTML yapısı aynı, sadece en dıştaki div'e bir ID ekledik -->
                <div id="gelisim-yorumu-karti">
                    <h6>📈 Gelişimi Nasıl Yorumluyoruz?</h6>
                    <p>
                    Bu grafikteki veriler <b>sadece öğrencinin hata yaptığı anları</b> içerir. Bu nedenle "gelişim", bir konuyu doğru yapma oranı değil, bir hatayla karşılaşıldığında <b>harcanan ortalama düşünme süresinin (yanıt süresinin) zamanla azalması</b> olarak yorumlanır. Düşen bir çizgi, öğrencinin konulara aşinalığının arttığını ve bir zorluk anında daha hızlı düşünebildiğini gösteren <b>pozitif bir işarettir.</b>
                    </p>
                </div>
            """, unsafe_allow_html=True)

            if not df_resampled.empty and len(df_resampled) > 1:
                ilk_deger = df_resampled['Ortalama Yanıt Süresi'].iloc[0]
                son_deger = df_resampled['Ortalama Yanıt Süresi'].iloc[-1]
                trend_yonu = "bir azalış" if son_deger < ilk_deger else "bir artış"

                en_yuksek_row = df_resampled.loc[df_resampled['Ortalama Yanıt Süresi'].idxmax()]
                en_yuksek_tarih = en_yuksek_row['Tarih'].strftime('%d %b %Y')

                en_dusuk_row = df_resampled.loc[df_resampled['Ortalama Yanıt Süresi'].idxmin()]
                en_dusuk_tarih = en_dusuk_row['Tarih'].strftime('%d %b %Y')

                st.markdown(f"**Analiz: {period} {level} Trendi**")

                if period == "Günlük":
                    st.warning(
                        "**Not:** Günlük veriler anlık dalgalanmalardan etkilenebilir. Genel eğilimi görmek için haftalık veya aylık bakış daha sağlıklı sonuçlar verir.")

                st.write(
                    f"Grafiğin genel yönü, düşünme hızında **{trend_yonu}** gösterdiğini işaret ediyor. "
                    f"Analizin ilk döneminde ortalama **{ilk_deger:.1f} saniye** olan hata yanıt süresi, "
                    f"son dönemde **{son_deger:.1f} saniyeye** ulaşmış durumda. "
                    f"En dikkat çekici an, **{en_yuksek_tarih}** tarihinde yaşanan yavaşlama ve en hızlı olunan **{en_dusuk_tarih}** tarihidir."
                )

                if period in ["Haftalık", "Aylık"]:
                    st.markdown("<h5 style='margin-top: 1rem;'>Ne Yapabilirsiniz?</h5>", unsafe_allow_html=True)
                    if son_deger < ilk_deger:
                        st.success(f"""
                            **Harika İlerleme!** Bu {period.lower()} eğilim, öğrencinin konseptlere daha hakim hale geldiğinin ve zorlandığı anlarda bile daha akıcı düşünebildiğinin bir göstergesi.
                            - **Başarıyı Vurgulayın:** Bu grafiği kendisine de göstererek "Bak, ne kadar hızlanmışsın! Çaban işe yarıyor." gibi cümlelerle motivasyonunu artırın.
                            - **Zirve Anlarını İnceleyin:** Grafikteki ani yükselişin olduğu **{en_yuksek_tarih}** civarındaki hataları "Bilge Danışman" sekmesinden kontrol ederek bu konuları pekiştirin.
                        """)
                    else:
                        st.error(f"""
                            **Bir Sinyal Var!** Bu {period.lower()} eğilim, son zamanlarda karşılaşılan konuların zorlaştığına veya odaklanmada bir güçlük yaşandığına işaret ediyor olabilir. Amaç, bu sinyali bir öğrenme fırsatına çevirmek.
                            - **Yavaşlamanın Nedenini Keşfedin:** Grafikteki yükselişin olduğu **{en_yuksek_tarih}** civarındaki hataları "Bilge Danışman" sekmesinden inceleyin. Özellikle "🧠 Kavramsal Zorluk" etiketi olan hatalar size yol gösterecektir.
                            - **Temellere Dönün:** Zorlandığı anlaşılan konularla ilgili temel egzersizlere kısa bir dönüş yapmak, özgüvenini yeniden kazanmasına yardımcı olabilir.
                        """)
            else:
                st.warning("Seçilen filtreler için yeterli veri bulunamadı.")

        # 5. BÖLÜM: Öğrenme Stilleri Analizi
        with st.expander("🧠 Öğrenme Stilleri Analizi: Öğrencinin Zorluklarla Başa Çıkma Tarzı", expanded=False):

            # --- BÖLÜM 1: KONSEPT VE ANALİZ MANTIĞI ---

            # Analiz için gerekli veriyi kopyala
            df_style = student_df_base[['Tekrar Sayısı', 'Yanıt Süresi (sn)', 'Oyun Tipi']].copy()

            if not df_style.empty and len(df_style) > 1:
                # Kadran sınırları için medyan değerlerini hesapla
                median_reaction = df_style['Yanıt Süresi (sn)'].median()
                median_repeat = df_style['Tekrar Sayısı'].median()


                # Her bir hatanın hangi öğrenme stiline ait olduğunu belirle
                def assign_style(row):
                    is_high_repeat = row['Tekrar Sayısı'] > median_repeat
                    is_high_reaction = row['Yanıt Süresi (sn)'] > median_reaction

                    if is_high_repeat and is_high_reaction:
                        return "🧠 Azimli Kâşif"
                    elif is_high_repeat and not is_high_reaction:
                        return "⚡ Enerjik Deneyici"
                    elif not is_high_repeat and is_high_reaction:
                        return "🤔 Dikkatli Düşünür"
                    else:  # not is_high_repeat and not is_high_reaction
                        return "💨 Hızlı Stratejist"


                df_style['Öğrenme Stili'] = df_style.apply(assign_style, axis=1)

                # --- BÖLÜM 2: GÖRSELLEŞTİRME VE ARAYÜZ ---

                # Renk ve ikon haritası
                style_map = {
                    "🧠 Azimli Kâşif": {"color": "#5DADE2", "icon": "🧠"},
                    "⚡ Enerjik Deneyici": {"color": "#F5B041", "icon": "⚡"},
                    "🤔 Dikkatli Düşünür": {"color": "#58D68D", "icon": "🤔"},
                    "💨 Hızlı Stratejist": {"color": "#EC7063", "icon": "💨"}
                }

                fig_scatter = px.scatter(
                    df_style,
                    x='Tekrar Sayısı',
                    y='Yanıt Süresi (sn)',
                    color='Öğrenme Stili',
                    color_discrete_map={k: v['color'] for k, v in style_map.items()},
                    hover_name='Oyun Tipi',
                    template='plotly_dark',
                    title='Hata Anındaki Öğrenme Stilleri Haritası'
                )

                # Kadran sınır çizgilerini ekle
                fig_scatter.add_vline(x=median_repeat, line_width=1, line_dash="dash", line_color="gray")
                fig_scatter.add_hline(y=median_reaction, line_width=1, line_dash="dash", line_color="gray")

                # Kadran arkaplan renklerini ekle (şekillerle)
                fig_scatter.add_shape(type="rect", x0=median_repeat, y0=median_reaction,
                                      x1=df_style['Tekrar Sayısı'].max(),
                                      y1=df_style['Yanıt Süresi (sn)'].max(),
                                      fillcolor=style_map["🧠 Azimli Kâşif"]['color'], opacity=0.1, layer="below",
                                      line_width=0)
                fig_scatter.add_shape(type="rect", x0=median_repeat, y0=df_style['Yanıt Süresi (sn)'].min(),
                                      x1=df_style['Tekrar Sayısı'].max(), y1=median_reaction,
                                      fillcolor=style_map["⚡ Enerjik Deneyici"]['color'], opacity=0.1, layer="below",
                                      line_width=0)
                fig_scatter.add_shape(type="rect", x0=df_style['Tekrar Sayısı'].min(), y0=median_reaction,
                                      x1=median_repeat,
                                      y1=df_style['Yanıt Süresi (sn)'].max(),
                                      fillcolor=style_map["🤔 Dikkatli Düşünür"]['color'], opacity=0.1, layer="below",
                                      line_width=0)
                fig_scatter.add_shape(type="rect", x0=df_style['Tekrar Sayısı'].min(),
                                      y0=df_style['Yanıt Süresi (sn)'].min(), x1=median_repeat, y1=median_reaction,
                                      fillcolor=style_map["💨 Hızlı Stratejist"]['color'], opacity=0.1, layer="below",
                                      line_width=0)

                fig_scatter.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    xaxis_title="Israr Seviyesi (Tekrar Sayısı)",
                    yaxis_title="Düşünme Süresi (Saniye)",
                    legend_title="Öğrenme Stilleri"
                )

                # Değişiklik burada: Orijinal st.plotly_chart yerine yeni fonksiyonu kullanıyoruz.
                display_chart_without_toolbar(fig_scatter)

                # --- BÖLÜM 3: POZİTİF VE YOL GÖSTERİCİ YORUMLAMA ---
                st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)
                st.subheader("Akıllı Analiz ve Destek Stratejileri")

                # Baskın stili bul
                dominant_style = df_style['Öğrenme Stili'].mode()[0]

                st.markdown(
                    f"""
                    <div style="border-radius: 8px; padding: 1rem; background-color: #262730; border: 1px solid #444;">
                        <h6 style="margin-top: 0; color: #A9CCE3;">Öğrencinin Hata Anındaki Baskın Öğrenme Stili:</h6>
                        <p style="color: #BDC3C7; font-size: 1rem;">
                        Bu grafik, öğrencinin bir zorlukla karşılaştığında sergilediği doğal eğilimleri gösterir. Şu anki baskın yaklaşımı, <b style="color:{style_map[dominant_style]['color']};">{dominant_style}</b> stilidir. Bu, onun bir problemi çözmeye çalışırkenki güçlü yönünü temsil eder. Amacımız, bu güçlü yönü desteklerken diğer yaklaşımları da denemesi için onu cesaretlendirmektir.
                        </p>
                    </div>
                    """, unsafe_allow_html=True
                )

                st.markdown(
                    f"""
                    <div style="margin-top: 20px;">
                        <h5 style="color: #FFFFFF;">Her Öğrenme Stili İçin Destek Stratejileri:</h5>
                        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;">
                            <div style="border-radius: 8px; padding: 1rem; background-color: #262730;">
                                <h6 style="margin-top:0; color:{style_map['🧠 Azimli Kâşif']['color']};">🧠 Azimli Kâşif İçin:</h6>
                                <p style="color: #BDC3C7; font-size: 0.9rem;">Bu harika azmi takdir edin! Tıkandığı noktada, ona doğru cevabı vermek yerine "Başka nasıl düşünebiliriz?" diye sorarak yol gösterin. Mücadelesi, en kalıcı öğrenmeleri sağlayacaktır.</p>
                            </div>
                            <div style="border-radius: 8px; padding: 1rem; background-color: #262730;">
                                <h6 style="margin-top:0; color:{style_map['⚡ Enerjik Deneyici']['color']};">⚡ Enerjik Deneyici İçin:</h6>
                                <p style="color: #BDC3C7; font-size: 0.9rem;">Bu enerjiyi doğruya yönlendirelim! "Harika bir hız! Şimdi bir de yavaşça, sorunun ne istediğine odaklanarak deneyelim mi?" diyerek onu düşünmeye davet edin. Enerjisi, doğru stratejiyle birleşince harikalar yaratır.</p>
                            </div>
                            <div style="border-radius: 8px; padding: 1rem; background-color: #262730;">
                                <h6 style="margin-top:0; color:{style_map['🤔 Dikkatli Düşünür']['color']};">🤔 Dikkatli Düşünür İçin:</h6>
                                <p style="color: #BDC3C7; font-size: 0.9rem;">Bu özenli yaklaşımı çok değerli! Hata yapmanın, öğrenme sürecinin doğal bir parçası olduğunu hatırlatın. "Yanlış yapmaktan korkma, en kötü ne olabilir ki? Birlikte düzeltiriz." diyerek onu cesaretlendirin.</p>
                            </div>
                            <div style="border-radius: 8px; padding: 1rem; background-color: #262730;">
                                <h6 style="margin-top:0; color:{style_map['💨 Hızlı Stratejist']['color']};">💨 Hızlı Stratejist İçin:</h6>
                                <p style="color: #BDC3C7; font-size: 0.9rem;">Bu akıcılığı korumak güzel! Bazen en zorlu soruların, üzerinde biraz daha durunca çözülen "gizli hazineler" olduğunu anlatın. Sadece bir soruya daha şans vermesini isteyerek dayanıklılığını artırabilirsiniz.</p>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True
                )

            else:
                st.warning("Öğrenme stilleri analizi için yeterli veri bulunamadı.")
        # 6. BÖLÜM: Haftalık Verimlilik Ritmi
        with st.expander("📅 Haftalık Verimlilik Ritmi: En Verimli Günleri Keşfedin", expanded=False):

            # --- BÖLÜM 1: ARKA PLAN MANTIĞI VE VERİ İŞLEMESİ ---

            # Analiz için gerekli veriyi grupla ve ikili metrikleri hesapla
            daily_analysis = student_df_base.groupby('Haftanın Günü').agg(
                Ortalama_Yanıt_Süresi=('Yanıt Süresi (sn)', 'mean'),
                Toplam_Hata_Sayısı=('Oyun Tipi', 'size')
            ).reset_index()

            # Haftanın günlerini doğru sıralamak için bir sıralama listesi oluştur
            days_order = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
            daily_analysis['Haftanın Günü'] = pd.Categorical(daily_analysis['Haftanın Günü'], categories=days_order,
                                                             ordered=True)
            daily_analysis = daily_analysis.sort_values('Haftanın Günü')

            if not daily_analysis.empty:
                # --- BÖLÜM 2: GÖRSELLEŞTİRME VE ARAYÜZ (UI) ---

                fig_radar = go.Figure()

                fig_radar.add_trace(go.Scatterpolar(
                    r=daily_analysis['Ortalama_Yanıt_Süresi'],
                    theta=daily_analysis['Haftanın Günü'],
                    mode='markers',
                    marker=dict(
                        size=daily_analysis['Toplam_Hata_Sayısı'],
                        sizemin=5,  # En küçük noktanın minimum boyutu
                        sizeref=daily_analysis['Toplam_Hata_Sayısı'].max() / 50,  # Boyutlandırma referansı
                        color=daily_analysis['Ortalama_Yanıt_Süresi'],
                        colorscale="Viridis_r",  # Tersine çevrilmiş (düşük değerler parlak)
                        colorbar_title="Yanıt Süresi (sn)",
                        showscale=True
                    ),
                    # İnteraktif Tooltip
                    customdata=daily_analysis[['Toplam_Hata_Sayısı']],
                    hovertemplate=(
                        "<b>%{theta}</b><br><br>"
                        "Ortalama Yanıt Süresi: <b>%{r:.1f} sn</b><br>"
                        "Toplam Hata Sayısı: <b>%{customdata[0]}</b>"
                        "<extra></extra>"
                    )
                ))

                fig_radar.update_layout(
                    title='Haftalık Verimlilik Haritası',
                    template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    polar=dict(
                        radialaxis=dict(visible=True, title='Düşünme Hızı (Saniye)')
                    ),
                    showlegend=False
                )

                # Değişiklik burada: Orijinal st.plotly_chart yerine yeni fonksiyonu kullanıyoruz.
                display_chart_without_toolbar(fig_radar)

                # --- BÖLÜM 3: DİNAMİK YORUMLAMA VE EYLEM PLANI KUTUSU ---
                st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)
                st.subheader("Haftalık Ritim Analizi ve Eylem Planı")

                # Dinamik verileri hesapla
                en_hizli_gun_df = daily_analysis.loc[daily_analysis['Ortalama_Yanıt_Süresi'].idxmin()]
                en_hizli_gun = en_hizli_gun_df['Haftanın Günü']
                en_hizli_gun_hata_sayisi = en_hizli_gun_df['Toplam_Hata_Sayısı']

                en_yavas_gun_df = daily_analysis.loc[daily_analysis['Ortalama_Yanıt_Süresi'].idxmax()]
                en_yavas_gun = en_yavas_gun_df['Haftanın Günü']
                en_yavas_gun_hata_sayisi = en_yavas_gun_df['Toplam_Hata_Sayısı']

                en_cok_hata_gun_df = daily_analysis.loc[daily_analysis['Toplam_Hata_Sayısı'].idxmax()]
                en_cok_hata_gun = en_cok_hata_gun_df['Haftanın Günü']

                st.markdown(f"""
                    <style>
                        .custom-info-box {{
                            border-radius: 8px; 
                            padding: 1.5rem; 
                            background-color: rgba(99, 110, 250, 0.1); 
                            border: 1px solid #636EFA;
                        }}
                        .custom-info-box h5, 
                        .custom-info-box p, 
                        .custom-info-box li {{
                            /* Streamlit'in tema değişkenini kullanarak rengi otomatik ayarla */
                            color: var(--text-color); 
                        }}
                        .custom-info-box h5 {{
                            margin-top: 0; 
                            font-weight: bold;
                        }}
                        .custom-info-box p {{
                            font-size: 0.9rem;
                        }}
                        .custom-info-box hr {{
                            border-top: 1px solid #333; 
                            margin: 1rem 0;
                        }}
                    </style>

                    <div class="custom-info-box">
                        <h5>Grafiği Nasıl Okumalısınız?</h5>
                        <p>
                        Bu grafik, öğrencinin haftalık verimlilik döngüsünü gösterir. Her bir noktanın iki anlamı vardır:
                        <ul>
                            <li><b>Konumu:</b> Noktanın merkeze yakınlığı, o gün hatalar üzerinde ne kadar <b>hızlı düşündüğünü</b> gösterir. (Merkeze yakın = Daha iyi)</li>
                            <li><b>Büyüklüğü:</b> Noktanın büyüklüğü, o gün <b>ne kadar çok hata yaptığını</b> gösterir. (Küçük nokta = Daha iyi)</li>
                        </ul>
                        </p>
                        <hr>
                        <h5>Haftalık Ritim Analizi:</h5>
                        <p>
                        <b>🚀 En Verimli Gün:</b> Grafiğe göre, <b>{en_hizli_gun}</b>, en verimli zaman dilimi olarak öne çıkıyor. Bu günde hem hatalar üzerinde hızlı düşünülmüş hem de hata sayısı ({en_hizli_gun_hata_sayisi}) nispeten az.
                        <br>
                        <b>🐌 Destek Gereken Gün:</b> En çok destek gereken gün ise <b>{en_yavas_gun}</b> gibi görünüyor. Bu günde hem düşünme süresi uzamış hem de ({en_yavas_gun_hata_sayisi}) hata yapılmış.
                        </p>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown(
                    f"""
                    <style>
                        .custom-advice-box {{
                            border-radius: 8px; 
                            padding: 1.5rem; 
                            background-color: rgba(184, 252, 197, 0.1); 
                            border: 1px solid #444; 
                            margin-top: 1rem;
                        }}
                        .custom-advice-box h5,
                        .custom-advice-box p,
                        .custom-advice-box li {{
                            /* Streamlit'in tema değişkenini kullanarak metin rengini otomatik ayarla */
                            color: var(--text-color);
                        }}
                        .custom-advice-box h5 {{
                            margin-top: 0; 
                            font-weight: bold;
                        }}
                        .custom-advice-box p {{
                            font-size: 0.9rem;
                        }}
                        .custom-advice-box ol {{
                            padding-left: 1.2rem;
                        }}
                        .custom-advice-box li {{
                            margin-bottom: 0.5rem;
                        }}
                    </style>

                    <div class="custom-advice-box">
                        <h5>Ne Yapabilirsiniz? Haftayı Akıllıca Planlayın</h5>
                        <p>
                        Bu ritmi anlamak, öğrencinin öğrenme sürecini daha verimli ve keyifli hale getirmek için bir fırsattır.
                        <ol>
                            <li><b>Verimli Günleri Fırsata Çevirin:</b> Öğrencinin en verimli olduğu <b>{en_hizli_gun}</b> gibi günlerde enerjisi ve odağı daha yüksek olabilir. Bu günleri, <b>yeni ve daha zorlayıcı konulara başlamak</b> için kullanmayı deneyin. Bu, yeni bilgileri daha kolay kavramasına yardımcı olabilir.</li>
                            <li><b>Destek Günlerini Yeniden Yapılandırın:</b> <b>{en_yavas_gun}</b> gibi günlerde haftanın yorgunluğu veya dikkat dağınıklığı görülebilir. Bu günlere yeni ve ağır konular yığmak yerine, daha önce öğrenilenleri pekiştirecek <b>kısa, eğlenceli ve ödüllendirici tekrar seansları</b> planlayabilirsiniz. Bu, hem özgüvenini artırır hem de onu bunaltmaz.</li>
                            <li><b>Yoğun Hata Günlerini Anlamlandırın:</b> Grafikte <b>{en_cok_hata_gun}</b> günündeki noktanın büyüklüğü, o gün yoğun bir çalışma yapıldığını veya zor bir konuyla karşılaşıldığını gösteriyor. O gün yapılan hataların doğasını (aceleci mi, kavramsal mı?) daha iyi anlamak için <b>"Bilge Danışman"</b> sekmesinden o günü inceleyebilirsiniz. Bu size, spesifik olarak hangi konuda desteğe ihtiyacı olduğunu gösterecektir.</li>
                        </ol>
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            else:
                st.warning("Haftalık verimlilik analizi için yeterli veri bulunamadı.")
        # 7. BÖLÜM: Kilit Güçlükler ve Çözüm Anahtarları
        with st.expander("🔑 Kilit Güçlükler ve Çözüm Anahtarları", expanded=False):

            # --- BÖLÜM 1: ARKA PLAN MANTIĞI ---

            # Analiz için gerekli sütunları içeren bir kopya oluştur
            df_lock_points = student_df_base[['question_id', 'Oyun Tipi', 'Kategori_kod',
                                              'Yanıt Süresi (sn)', 'Tekrar Sayısı',
                                              'Öğrencinin Cevabı', 'Doğru Cevap']].copy()

            if not df_lock_points.empty and 'question_id' in df_lock_points.columns:
                # 1. En sık yanlış yapılan 3 soruyu bul
                top_errors = df_lock_points['question_id'].value_counts().nlargest(3).reset_index()
                top_errors.columns = ['question_id', 'Hata Sayısı']

                if not top_errors.empty:
                    st.markdown(
                        "Öğrencinin en sık hata yaptığı 3 soru ve bu sorular için özel çözüm stratejileri aşağıdadır.")

                    # --- BÖLÜM 2: ARAYÜZ VE TASARIM (İNTERAKTİF KARTLAR) ---
                    cols = st.columns(len(top_errors))

                    for i, row in top_errors.iterrows():
                        with cols[i]:
                            question_id = row['question_id']
                            hata_sayisi = row['Hata Sayısı']

                            # 2. Bu 3 soru için detaylı verileri topla
                            question_data = df_lock_points[df_lock_points['question_id'] == question_id]
                            game_type = question_data['Oyun Tipi'].iloc[0]
                            category_kod = question_data['Kategori_kod'].iloc[0]
                            correct_answer = question_data['Doğru Cevap'].iloc[0]
                            most_common_wrong_answer = question_data['Öğrencinin Cevabı'].mode()[0]

                            avg_reaction_time = question_data['Yanıt Süresi (sn)'].mean()
                            avg_repeat_count = question_data['Tekrar Sayısı'].mean()

                            # Kartın Kapalı Hali
                            st.markdown(
                                f"""
                                <div style="border: 1px solid #444; border-radius: 8px; padding: 1rem; background-color: #FCE4EC; text-align: center;">
                                    <h6 style="color: #7A3B3B; margin-top: 0; font-weight: bold;">{i + 1}. Kilit Güçlük: {game_type}</h6>
                                    <p style="font-size: 2rem; font-weight: bold; margin: 0.5rem 0; color: #5D4037;">{hata_sayisi}</p>
                                    <p style="margin-bottom: 0; color: #5D4037;">Toplam Hata</p>
                                </div>
                                """, unsafe_allow_html=True
                            )

                            # --- BÖLÜM 3: İNTERAKTİFLİK VE DİNAMİK İÇERİK ---
                            # Kartın Açık Hali (st.expander içinde)
                            with st.expander("Çözüm Anahtarını Gör ▼"):

                                # Hata Analizi (Öğrenme Sinyali)
                                # Not: Burada tüm veri setinin ortalamasını değil, bu soruya özel ortalamaları kullanıyoruz
                                if avg_repeat_count > 1.5:  # Ortalama tekrar sayısı 1.5'tan fazlaysa
                                    sinyal_metni = "Bu sorudaki hatalar genellikle <b>🔁 Takılma Noktası</b> stilinde yapılıyor. Yani öğrenci bu soruda ısrarla denemesine rağmen doğruya ulaşmakta zorlanıyor."
                                elif avg_reaction_time > student_df_base[student_df_base['Oyun Tipi'] == game_type][
                                    'Yanıt Süresi (sn)'].mean() * 1.5:
                                    sinyal_metni = "Bu sorudaki hatalar genellikle <b>🧠 Kavramsal Zorluk</b> stilinde yapılıyor. Yani üzerinde düşünülüyor ama bir noktada takılıp kalınıyor."
                                else:
                                    sinyal_metni = "Bu sorudaki hatalar genellikle <b>⚡ Aceleci veya Dikkatsiz</b> bir yaklaşımla yapılıyor. Hızlı cevap verme eğilimi, hataya yol açıyor olabilir."

                                # Ne Yapabilirsiniz? (Çözüm Anahtarı)
                                if category_kod in ['letter', 'spelling']:
                                    cozum_anahtari = f"Bu spesifik harf/hece kuralını birlikte gözden geçirin. Cevapları ('<b>{most_common_wrong_answer}</b>' ve '<b>{correct_answer}</b>') yan yana bir kağıda yazarak aradaki farkı görsel olarak göstermek faydalı olabilir."
                                elif category_kod == 'direction':
                                    cozum_anahtari = "Bu soruyu evdeki nesnelerle (örn: 'Topu tavşanın sağına koy') canlandırarak oynayın. Somutlaştırmak, bu tür kavramların kalıcı olmasını sağlar."
                                elif category_kod in ['word', 'meaning']:
                                    cozum_anahtari = f"Bu iki kelime/cümlenin anlam farkı üzerine konuşun. 'Senin en sık yaptığın hata buymuş (<b>{most_common_wrong_answer}</b>), sence neden karıştırmış olabilirsin?' diye sorarak onun düşünce sürecini anlamaya çalışın."
                                else:
                                    cozum_anahtari = "Bu sorunun gerektirdiği temel beceriyi tekrar etmek ve benzer, daha kolay örneklerle başlamak özgüvenini artıracaktır."

                                st.markdown(
                                    f"""
                                    <div style="font-size: 0.9rem;">
                                        <p><b>Soru Detayları:</b></p>
                                        <ul>
                                            <li><b>Doğru Cevap:</b> "{correct_answer}"</li>
                                            <li><b>En Sık Yapılan Hata:</b> "{most_common_wrong_answer}"</li>
                                        </ul>
                                        <p><b>Hata Analizi (Öğrenme Sinyali):</b><br>{sinyal_metni}</p>
                                        <p><b>Ne Yapabilirsiniz? (Çözüm Anahtarı):</b><br>{cozum_anahtari}</p>
                                    </div>
                                    """, unsafe_allow_html=True
                                )
                else:
                    st.info("Belirgin bir takılma noktası tespit edilmedi.")
            else:
                st.info("Veri setinde 'question_id' bilgisi bulunmadığı için bu analiz yapılamadı.")
        # 8. BÖLÜM: Aktivite ve Verimlilik Analizi
        with st.expander("🕰️ Çalışma Alışkanlıkları: Aktivite ve Verimlilik Analizi", expanded=False):

            # --- BÖLÜM 1: ARKA PLAN MANTIĞI VE VERİ İŞLEMESİ ---

            # Zaman dilimlerine göre veriyi grupla ve ikili metrikleri hesapla
            time_analysis = student_df_base.groupby('Günün Zamanı').agg(
                Aktivite=('Oyun Tipi', 'size'),
                Verimlilik=('Yanıt Süresi (sn)', 'mean')
            ).reset_index()

            # Zaman dilimlerini doğru sıralamak için bir sıralama listesi oluştur
            time_order = ['Sabah (05-12)', 'Öğlen (12-18)', 'Akşam (18-22)', 'Gece (22-05)']
            time_analysis['Günün Zamanı'] = pd.Categorical(time_analysis['Günün Zamanı'], categories=time_order,
                                                           ordered=True)
            time_analysis = time_analysis.sort_values('Günün Zamanı')

            if not time_analysis.empty:
                # --- BÖLÜM 2: GÖRSELLEŞTİRME VE ARAYÜZ (UI) ---

                # Plotly'nin Subplots özelliğini kullanarak çift Y eksenli bir grafik oluştur
                fig_grouped_bar = go.Figure()

                # Bar 1: Aktivite (Hata Sayısı) - Sol Y Ekseni
                fig_grouped_bar.add_trace(go.Bar(
                    x=time_analysis['Günün Zamanı'],
                    y=time_analysis['Aktivite'],
                    name='Aktivite (Hata Sayısı)',
                    marker_color='#5DADE2',  # Mavi
                    yaxis='y1'
                ))

                # Bar 2: Verimlilik (Yanıt Süresi) - Sağ Y Ekseni
                fig_grouped_bar.add_trace(go.Bar(
                    x=time_analysis['Günün Zamanı'],
                    y=time_analysis['Verimlilik'],
                    name='Verimlilik (Ort. Yanıt Süresi)',
                    marker_color='#58D68D',  # Yeşil
                    yaxis='y2'
                ))

                fig_grouped_bar.update_layout(
                    title_text='Günün Saatlerine Göre Aktivite ve Verimlilik',
                    template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    barmode='group',
                    xaxis_title="Günün Zaman Dilimleri",
                    # Çift Y Ekseni Tanımlamaları
                    yaxis=dict(
                        title="Aktivite (Toplam Hata Sayısı)",
                        side='left'
                    ),
                    yaxis2=dict(
                        title="Verimlilik (Ortalama Yanıt Süresi - sn)",
                        overlaying='y',
                        side='right'
                    ),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )

                # Değişiklik burada: Orijinal st.plotly_chart yerine yeni fonksiyonu kullanıyoruz.
                display_chart_without_toolbar(fig_grouped_bar)

                # --- BÖLÜM 3: DİNAMİK "AKILLI ANALİZ VE ÖNERİ" KUTUSU ---
                st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)
                st.subheader("Akıllı Analiz ve Öneri")

                # Dinamik verileri hesapla
                en_aktif_zaman_row = time_analysis.loc[time_analysis['Aktivite'].idxmax()]
                en_aktif_zaman = en_aktif_zaman_row['Günün Zamanı']

                en_verimli_zaman_row = time_analysis.loc[time_analysis['Verimlilik'].idxmin()]
                en_verimli_zaman = en_verimli_zaman_row['Günün Zamanı']

                # Kutuları oluştur
                st.markdown(
                    f"""
                    <style>
                    /*
                      Bu stil bloğu, kutuların renklerini kullanıcının
                      seçtiği aydınlık veya karanlık moda göre mavi tonlarında ayarlar.
                    */
                    .themed-box-blue {{
                        border-radius: 8px;
                        padding: 1.5rem;
                        border-width: 1px;
                        border-style: solid;
                    }}
                    .themed-box-blue h5 {{
                        margin-top: 0;
                        font-weight: bold;
                    }}
                    .themed-box-blue p, .themed-box-blue li {{
                        font-size: 0.9rem;
                    }}
                    .themed-box-blue hr {{
                        margin: 1rem 0;
                        border: none; /* Kenarlık rengi aşağıda modlara göre ayarlanacak */
                    }}

                    /* === AYDINLIK MOD (AÇIK MAVİ TEMA) === */
                    @media (prefers-color-scheme: light) {{
                        .themed-box-blue {{
                            background-color: #EBF5FB; /* Çok açık pastel mavi */
                            border-color: #AED6F1;    /* Belirgin ama yumuşak mavi kenarlık */
                        }}
                        .themed-box-blue h5 {{ color: #2874A6; }}  /* Koyu, okunaklı mavi başlık */
                        .themed-box-blue p, .themed-box-blue li, .themed-box-blue b {{ color: #17202A; }} /* Koyu, okunaklı metin */
                        .themed-box-blue hr {{ border-top: 1px solid #D6EAF8; }}
                    }}

                    /* === KARANLIK MOD (KOYU MAVİ TEMA) === */
                    @media (prefers-color-scheme: dark) {{
                        .themed-box-blue {{
                            background-color: #2C3E50; /* Koyu, profesyonel lacivert */
                            border-color: #566573;    /* Daha açık, belli belirsiz kenarlık */
                        }}
                        .themed-box-blue h5 {{ color: #A9CCE3; }} /* Açık, pastel mavi başlık */
                        .themed-box-blue p, .themed-box-blue li, .themed-box-blue b {{ color: #E5E7E9; }} /* Açık ve okunaklı metin */
                        .themed-box-blue hr {{ border-top: 1px solid #566573; }}
                    }}
                    </style>

                    <div class="themed-box-blue">
                        <h5>Grafiği Nasıl Okumalısınız?</h5>
                        <p>
                        Bu grafik, öğrencinin gün içindeki aktivite ve verimlilik anlarını karşılaştırır:
                        <ul>
                            <li><b>Mavi Barlar (Aktivite):</b> Ne kadar uzunsa, o saatlerde o kadar <b>çok hata yapıldığını</b> gösterir.</li>
                            <li><b>Yeşil Barlar (Verimlilik):</b> Ne kadar kısaysa, o saatlerde hatalar üzerinde o kadar <b>hızlı düşünüldüğünü</b> (daha verimli olunduğunu) gösterir.</li>
                        </ul>
                        </p>
                        <hr>
                        <h5>Analiz:</h5>
                        <p>
                        🕒 <b>En Aktif Zaman:</b> Öğrenci en çok <b>{en_aktif_zaman}</b> saatlerinde egzersiz yapıyor.<br>
                        🧠 <b>En Verimli Zaman:</b> Buna karşılık, en verimli (en hızlı) olduğu zaman dilimi ise <b>{en_verimli_zaman}</b>.
                        </p>
                    </div>
                    """, unsafe_allow_html=True
                )

                st.markdown(
                    f"""
                    <div class="themed-box-blue" style="margin-top: 1rem;">
                        <h5>Ne Yapabilirsiniz? "Altın Saatleri" Keşfedin</h5>
                        <div style="font-size: 0.9rem;">
                    """, unsafe_allow_html=True
                )
                # Koşullu önerileri göster (Bu kısım hiç değiştirilmedi)
                if en_aktif_zaman == en_verimli_zaman:
                    st.success(
                        f"""
                        **Harika!** Öğrencinin en çok çalıştığı **{en_aktif_zaman}** saatleri, aynı zamanda en verimli olduğu zamanlar. Bu onun için "altın saatler". Bu ritmi korumaya devam edin ve en önemli konuları bu zaman dilimine yerleştirmeye çalışın.
                        """
                    )
                else:
                    st.warning(
                        f"""
                        **Önemli Bir Fırsat!** Öğrenci en çok **{en_aktif_zaman}** saatlerinde çalışıyor ancak en verimli olduğu zamanlar **{en_verimli_zaman}**. Bu, yorgunken daha fazla çaba sarf ediyor olabileceğini gösteriyor.

                        **Öneri:** Mümkünse, **{en_aktif_zaman}**'ndeki çalışma seanslarının bir kısmını, onun doğal olarak daha verimli olduğu **{en_verimli_zaman}** saatlerine kaydırmayı deneyin. Bu basit değişiklik, daha az eforla daha fazla başarı getirebilir.
                        """
                    )

                st.markdown("</div></div>", unsafe_allow_html=True)

        # 10. BÖLÜM: Gelişim Odaklı Efor Analizi
        with st.expander("💡 Gelişim Odaklı Efor Analizi: Harcanan Çabanın Geri Dönüşü", expanded=False):

            # --- BÖLÜM 1: ARKA PLAN MANTIĞI ---

            df_effort = student_df_base.sort_values('datetime').copy()

            if not df_effort.empty and len(df_effort) > 20:

                df_effort['Efor (Toplam Hata Sayısı)'] = range(1, len(df_effort) + 1)
                df_effort['Düşünme Hızı (Ort. Yanıt Süresi)'] = df_effort['Yanıt Süresi (sn)'].rolling(window=20,
                                                                                                       min_periods=1).mean()

                peak_idx = df_effort['Düşünme Hızı (Ort. Yanıt Süresi)'].idxmax()
                trough_idx = df_effort['Düşünme Hızı (Ort. Yanıt Süresi)'].idxmin()
                highlight_points = pd.concat([df_effort.loc[[peak_idx]], df_effort.loc[[trough_idx]]])
                highlight_points['Açıklama'] = ['En Yavaş An (Zorlanma Zirvesi)', 'En Hızlı An (Verimlilik Zirvesi)']

                # --- BÖLÜM 2: GÖRSELLEŞTİRME (YENİ STİL) ---

                # Ana figürü oluştur
                fig_effort = go.Figure()

                # 1. Katman: Mavi Alan Grafiği (Area Chart)
                # Dolgu rengi için saydam (opacity'li) bir mavi tonu kullanıyoruz
                fig_effort.add_trace(go.Scatter(
                    x=df_effort['Efor (Toplam Hata Sayısı)'],
                    y=df_effort['Düşünme Hızı (Ort. Yanıt Süresi)'],
                    fill='tozeroy',  # Aşağı doğru doldur
                    mode='none',  # Çizgiyi gösterme, sadece alanı doldur
                    fillcolor='rgba(93, 173, 226, 0.2)',  # Yarı saydam açık mavi
                    name='Verimlilik Alanı',
                    hoverinfo='none'  # Bu katman için tooltip'i kapat
                ))

                # 2. Katman: Belirgin Trend Çizgisi (Line Chart)
                # Alanla kontrast oluşturacak daha canlı bir renk seçiyoruz
                fig_effort.add_trace(go.Scatter(
                    x=df_effort['Efor (Toplam Hata Sayısı)'],
                    y=df_effort['Düşünme Hızı (Ort. Yanıt Süresi)'],
                    mode='lines',
                    line=dict(color='#E74C3C', width=3),  # Belirgin bir kırmızı renk
                    name='Gelişim Trendi'
                ))

                # 3. Katman: İnteraktif Kilit Anlar Noktaları
                fig_effort.add_trace(go.Scatter(
                    x=highlight_points['Efor (Toplam Hata Sayısı)'],
                    y=highlight_points['Düşünme Hızı (Ort. Yanıt Süresi)'],
                    mode='markers',
                    marker=dict(size=12, color='#F39C12', symbol='circle-open', line=dict(width=3)),
                    # Belirgin bir turuncu
                    name='Kilit Anlar',
                    customdata=highlight_points[['Açıklama']],
                    hovertemplate="<b>%{customdata[0]}</b><br>Efor: %{x}<br>Hız: %{y:.1f} sn<extra></extra>"
                ))

                fig_effort.update_layout(
                    title_text='Harcanan Eforun Düşünme Hızına Etkisi',
                    template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color="#FFFFFF",
                    showlegend=False,
                    xaxis_title='Harcanan Toplam Efor (Yapılan Hata Sayısı)',
                    yaxis_title='Düşünme Hızı (Ortalama Saniye)'
                )

                # Değişiklik burada: Orijinal st.plotly_chart yerine yeni fonksiyonu kullanıyoruz.
                display_chart_without_toolbar(fig_effort)

                # --- BÖLÜM 3: AKILLI ANALİZ VE FAYDA RAPORU (DEĞİŞİKLİK YOK) ---
                st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)
                st.subheader("Fayda Analizi ve Eylem Planı")

                baslangic_hizi = df_effort['Düşünme Hızı (Ort. Yanıt Süresi)'].iloc[0]
                mevcut_hiz = df_effort['Düşünme Hızı (Ort. Yanıt Süresi)'].iloc[-1]
                iyilesme_orani = ((baslangic_hizi - mevcut_hiz) / baslangic_hizi) * 100 if baslangic_hizi > 0 else 0

                st.markdown(f"""
                    <div style="border-radius: 8px; padding: 1.5rem; background-color: #2C2F33; border: 1px solid #444;">
                        <h5 style="color: #A9CCE3; margin-top: 0; font-weight: bold;">Bu Grafik Ne Anlatıyor?</h5>
                        <p style="color: #BDC3C7;">
                        Bu grafik, öğrencinin platformda harcadığı <b>toplam çabanın (yatay eksen)</b>, onun bir hata anındaki <b>verimliliğini (dikey eksen)</b> ne kadar geliştirdiğini gösterir. Verimlilik, bir hatayı çözmek için harcanan ortalama düşünme süresidir. Bu nedenle, <b>çizginin aşağı inmesi, daha az sürede daha etkili düşündüğünü ve geliştiğini gösterir.</b>
                        </p>
                        <hr style="border-top: 1px solid #333; margin: 1.5rem 0;">
                        <h5 style="color: #A9CCE3; font-weight: bold;">Trend Analizi ve Öneriler</h5>
                        <div style="display:flex; flex-wrap: wrap; gap: 20px; margin-top: 10px;">
                            <div style="flex:1; min-width: 300px;">
                                <h6 style="color: #58D68D;">✅ Grafikteki İnişler (Pozitif Sinyal)</h6>
                                <p style="color: #BDC3C7; font-size: 0.9rem;">
                                <b>Anlamı:</b> Çizginin aşağı yönlü olduğu her an, öğrencinin konulara daha hakim hale geldiğinin ve zorlandığı anlarda bile daha hızlı ve akıcı düşünebildiğinin bir kanıtıdır. Bu, harcanan eforun karşılığının alındığı anlamına gelir.<br>
                                <b>Ne Yapabilirsiniz?:</b> Bu başarıyı ona da göstererek motivasyonunu artırın. Gelişimin en belirgin olduğu anları kutlayın ve bu tutarlılığı koruması için onu teşvik edin.
                                </p>
                            </div>
                            <div style="flex:1; min-width: 300px;">
                                <h6 style="color: #EC7063;">⚠️ Grafikteki Yükselişler (Dikkat Gerektiren Sinyal)</h6>
                                <p style="color: #BDC3C7; font-size: 0.9rem;">
                                <b>Anlamı:</b> Çizginin yukarı yönlü olduğu anlar, genellikle yeni ve daha zorlayıcı bir konuyla karşılaşıldığını veya o dönemde odaklanmada bir güçlük yaşandığını gösterir. Bu bir başarısızlık değil, desteğe en çok ihtiyaç duyduğu anı gösteren bir sinyaldir.<br>
                                <b>Ne Yapabilirsiniz?:</b> Grafikteki bu zirve noktalarına fare ile gelerek hangi dönemde yaşandığını görün. Ardından "Bilge Danışman" sekmesini kullanarak o dönemde yapılan "🧠 Kavramsal Zorluk" hatalarını inceleyerek sorunun kökenine inebilirsiniz.
                                </p>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True
                            )

            else:
                st.info(
                    "Bu analizin yapılabilmesi için en az 20 hata verisine ihtiyaç vardır. Lütfen platformu kullanmaya devam edin.")
    # --- TAB 2: BAŞARI ORANI HESAPLAMASI VE BÖLÜMLERİN AYRILMASI ---
    with tab2:
        st.header("Egzersiz Bazında Haftalık İlerleme Detayları")

        # --- BÖLÜM 1: HAFTALIK İLERLEME ANALİZİ (ÜST KISIM) ---
        col1, col2 = st.columns(2)
        with col1:
            egzersizler = ["Tüm Egzersizler"] + sorted(student_df_base['Oyun Tipi'].unique())
            secilen_egzersiz = st.selectbox("Analiz etmek istediğiniz egzersiz türünü seçin:", egzersizler,
                                            key="haftalik_egzersiz_secim")

        with col2:
            max_hafta_numarasi = student_df_base['Eğitim Haftası'].max()
            hafta_secenekleri = [h for h in [4, 6, 8] if h <= max_hafta_numarasi]
            if max_hafta_numarasi > 1 and max_hafta_numarasi not in hafta_secenekleri:
                hafta_secenekleri.append(max_hafta_numarasi)
            gecerli_secenekler = sorted(list(set(hafta_secenekleri)))

            if not gecerli_secenekler:
                hafta_sayisi = max_hafta_numarasi
            else:
                hafta_sayisi = st.radio("Gelişimi görmek istediğiniz dönemi seçin:",
                                        options=gecerli_secenekler,
                                        format_func=lambda x: f"İlk {x} Hafta" if x != max_hafta_numarasi else "Tümü",
                                        index=len(gecerli_secenekler) - 1, horizontal=True, key="hafta_donem_secim")

        # Bu DataFrame SADECE üst bölümdeki haftalık gelişim grafiği için kullanılır.
        df_progress_filtered = student_df_base[student_df_base['Eğitim Haftası'] <= hafta_sayisi]
        if secilen_egzersiz != "Tüm Egzersizler":
            df_progress_filtered = df_progress_filtered[df_progress_filtered['Oyun Tipi'] == secilen_egzersiz]

        if df_progress_filtered.empty or len(df_progress_filtered['Eğitim Haftası'].unique()) < 1:
            st.warning(f"Seçilen kriterler için gösterilecek veri bulunmamaktadır.")
        else:
            # Üst bölümdeki grafik ve raporlar için hesaplamalar (Değişiklik yok)
            all_weeks = pd.DataFrame({'Eğitim Haftası': range(1, hafta_sayisi + 1)})
            weekly_stats = df_progress_filtered.groupby('Eğitim Haftası', as_index=False).agg(
                Hata_Sayısı=('datetime', 'size'),
                Egzersiz_Sayısı=('Oyun Tipi', pd.Series.nunique)
            )
            weekly_stats = pd.merge(all_weeks, weekly_stats, on='Eğitim Haftası', how='left')
            weekly_stats['Hafta Etiketi'] = "Hafta " + weekly_stats['Eğitim Haftası'].astype(str)

            if secilen_egzersiz == "Tüm Egzersizler":
                weekly_stats['Toplam_Soru'] = weekly_stats['Egzersiz_Sayısı'] * 10
                weekly_stats['Başarı Oranı (%)'] = weekly_stats.apply(
                    lambda row: ((row['Toplam_Soru'] - row['Hata_Sayısı']) / row['Toplam_Soru'] * 100) if row[
                                                                                                              'Toplam_Soru'] > 0 else 100,
                    axis=1)
                grafik_basligi = "Haftalık Toplam Hata ve Ortalama Başarı Oranı"
            else:
                TOTAL_QUESTIONS_PER_EXERCISE = 10
                weekly_stats['Başarı Oranı (%)'] = (
                        (TOTAL_QUESTIONS_PER_EXERCISE - weekly_stats[
                            'Hata_Sayısı']) / TOTAL_QUESTIONS_PER_EXERCISE * 100)
                grafik_basligi = "Haftalık Hata Sayısı ve Başarı Oranı Kıyaslaması"

            weekly_stats['Başarı Oranı (%)'] = weekly_stats['Başarı Oranı (%)'].clip(lower=0).fillna(0)
            weekly_stats['Hata_Sayısı'] = weekly_stats['Hata_Sayısı'].fillna(0)
            weekly_stats['Önceki_Hafta_Hata_Sayısı'] = weekly_stats['Hata_Sayısı'].shift(1)


            def format_degisim_metni(row):
                current_errors = row['Hata_Sayısı']
                previous_errors = row['Önceki_Hafta_Hata_Sayısı']
                if pd.isna(previous_errors): return "Kıyaslama için önceki hafta verisi yok."
                if previous_errors == 0: return "Önceki hafta hiç hata yoktu." if current_errors > 0 else "Değişim yok, yine hatasız."
                degisim_yuzdesi = ((current_errors - previous_errors) / previous_errors) * 100
                if degisim_yuzdesi < 0:
                    return f"Önceki haftaya göre <b>%{abs(degisim_yuzdesi):.0f} daha az hata!</b>"
                elif degisim_yuzdesi > 0:
                    return f"Önceki haftaya göre %{degisim_yuzdesi:.0f} daha fazla hata."
                else:
                    return "Değişim yok."


            weekly_stats['Değişim Metni'] = weekly_stats.apply(format_degisim_metni, axis=1)

            st.subheader(f"'{secilen_egzersiz}' Alanında Haftalık Gelişim")
            fig_combo = go.Figure()
            fig_combo.add_trace(
                go.Bar(x=weekly_stats['Hafta Etiketi'], y=weekly_stats['Hata_Sayısı'], name='Hata Sayısı'))
            fig_combo.add_trace(go.Scatter(
                x=weekly_stats['Hafta Etiketi'], y=weekly_stats['Başarı Oranı (%)'], name='Başarı Oranı', yaxis='y2',
                mode='lines+markers', line=dict(color='darkorange', width=3),
                customdata=weekly_stats[['Hata_Sayısı', 'Değişim Metni']],
                hovertemplate="<br>".join(
                    ["<b>%{x}</b>", "Başarı Oranı: %{y:.1f}%", "Toplam Hata Sayısı: %{customdata[0]:.0f}",
                     "%{customdata[1]}"]) + "<extra></extra>"))
            fig_combo.update_layout(title_text=grafik_basligi, template="plotly_dark",
                                    yaxis=dict(title="Toplam Hata Sayısı"),
                                    yaxis2=dict(title="Başarı Oranı (%)", overlaying='y', side='right',
                                                range=[-5, 105]),
                                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_combo, use_container_width=True)

            with st.container(border=True):
                st.markdown(f"##### ✨ Akıllı Rapor: '{secilen_egzersiz}' Gelişimi")

                # Analiz için sadece aktivite olan haftaları (NaN olmayan) filtrele.
                # Hata sayısı 0 olsa bile bu bir aktivitedir ve başarı %100 demektir.
                active_weeks = weekly_stats[weekly_stats['Hata_Sayısı'].notna()].copy()

                # --- 1. KENAR DURUMLARI KONTROLÜ ---
                if active_weeks.empty:
                    st.info(
                        f"Seçilen dönemde '{secilen_egzersiz}' egzersizi için gösterilecek herhangi bir aktivite verisi bulunmuyor.")

                elif (active_weeks['Hata_Sayısı'] == 0).all():
                    st.success(
                        "🎉 **Mükemmel Performans!** Seçilen dönem boyunca bu alanda hiç hata yapılmamış. Harika iş!")

                elif len(active_weeks) < 2:
                    st.info(
                        "📊 **Tek Haftalık Veri:** Gelişim trendini analiz edebilmek için en az iki haftalık veri gereklidir. "
                        f"Mevcut tek haftada ({active_weeks.iloc[0]['Hafta Etiketi']}) başarı oranı **%{active_weeks.iloc[0]['Başarı Oranı (%)']:.0f}** olarak kaydedilmiştir.")

                # --- 2. DETAYLI ANALİZ (En az 2 hafta veri varsa) ---
                else:
                    # a) Genel Trend Analizi (Dönemin başı ve sonu kıyaslaması)
                    ilk_hafta_veri = active_weeks.iloc[0]
                    son_hafta_veri = active_weeks.iloc[-1]
                    genel_degisim = son_hafta_veri['Başarı Oranı (%)'] - ilk_hafta_veri['Başarı Oranı (%)']

                    st.markdown("**Genel Trend**")
                    if genel_degisim > 10:
                        st.success(
                            f"📈 **Pozitif Yönelim:** {ilk_hafta_veri['Hafta Etiketi']} ile {son_hafta_veri['Hafta Etiketi']} arasında başarı oranında **%{genel_degisim:.0f} puanlık harika bir artış** gözlemleniyor.")
                    elif genel_degisim < -10:
                        st.warning(
                            f"📉 **Dikkat Gereken Yönelim:** Dönem başından sonuna kadar başarı oranında **%{abs(genel_degisim):.0f} puanlık bir düşüş** var. Bu alana odaklanmak faydalı olabilir.")
                    else:
                        st.info(
                            f"📊 **Stabil Seyir:** Başarı oranı, dönemin başı (%{ilk_hafta_veri['Başarı Oranı (%)']:.0f}) ve sonu (%{son_hafta_veri['Başarı Oranı (%)']:.0f}) arasında önemli bir değişiklik göstermiyor.")

                    st.divider()

                    # b) Öne Çıkan Haftalar (En iyi ve en zorlu hafta)
                    en_iyi_hafta = active_weeks.loc[active_weeks['Başarı Oranı (%)'].idxmax()]
                    en_zorlu_hafta = active_weeks.loc[active_weeks['Hata_Sayısı'].idxmax()]

                    st.markdown("**Performans Zirveleri**")
                    col1_rapor, col2_rapor = st.columns(2)
                    with col1_rapor:
                        st.markdown(
                            f"🏆 **En Yüksek Başarı:**<br> **{en_iyi_hafta['Başarı Oranı (%)']:.0f}%** oranıyla **{en_iyi_hafta['Hafta Etiketi']}**.",
                            unsafe_allow_html=True)
                    with col2_rapor:
                        st.markdown(
                            f"🧠 **En Çok Odaklanılan Hafta:**<br> **{en_zorlu_hafta['Hata_Sayısı']:.0f} hata** ile **{en_zorlu_hafta['Hafta Etiketi']}**.",
                            unsafe_allow_html=True)

                    st.divider()

                    # c) Tutarlılık ve Son Durum Analizi
                    st.markdown("**Tutarlılık ve Son Durum**")
                    basari_stdev = active_weeks['Başarı Oranı (%)'].std()
                    if basari_stdev < 7.5:
                        st.info(
                            "✔️ **İstikrarlı Performans:** Başarı oranları haftadan haftaya çok az değişiklik gösteriyor. Bu, tutarlı bir çalışma temposunun işareti.")
                    else:
                        st.warning(
                            "⚠️ **Dalgalı Performans:** Haftalık başarı oranları arasında belirgin farklar var. Bu, bazı haftaların daha zorlu geçtiğini veya çalışma düzeninde değişiklikler olduğunu gösterebilir.")

                    # Son haftanın durumunu, zaten hesaplanmış olan 'Değişim Metni' üzerinden yorumla
                    # .iloc[-1] kullanarak her zaman en son haftayı seçtiğimizden emin oluyoruz.
                    son_hafta_yorumu = weekly_stats.dropna(subset=['Hata_Sayısı']).iloc[-1]['Değişim Metni']
                    if "daha az hata" in son_hafta_yorumu:
                        st.success(f"👍 **Son hafta harika bir ilerleme var:** {son_hafta_yorumu}")
                    elif "daha fazla hata" in son_hafta_yorumu:
                        st.warning(f"👎 **Son haftaya dikkat:** {son_hafta_yorumu}")
                    else:
                        st.info(f"👌 {son_hafta_yorumu}")

        # --- BÖLÜM 2: GÜNLÜK DETAY ANALİZİ (ALT KISIM) - BAĞIMSIZ HALE GETİRİLDİ ---

        st.subheader("Seçilen Hafta İçin Günlük Detay Analizi")

        # YENİ KOD: Alt bölümün, üstteki egzersiz filtresinden etkilenmemesi için
        # YALNIZCA hafta dönemi filtresini (`hafta_sayisi`) kullanarak yeni bir df oluşturuyoruz.
        df_for_daily_analysis = student_df_base[student_df_base['Eğitim Haftası'] <= hafta_sayisi]

        # DEĞİŞİKLİK: Haftaları, filtrelenmemiş (sadece hafta dönemine göre filtrelenmiş) veriden alıyoruz.
        haftalar = sorted(df_for_daily_analysis['Eğitim Haftası'].unique())

        if haftalar:
            secilen_hafta = st.selectbox(
                "Analiz etmek istediğiniz eğitim haftasını seçin:",
                options=haftalar,
                format_func=lambda x: f"Hafta {x}",
                key="gunluk_hafta_secim"  # Anahtar (key) benzersiz olmalı, bu yüzden aynı kalabilir.
            )

            # DEĞİŞİKLİK: df_secilen_hafta'yı üstte filtrelenmiş df'den değil, bu bölüme özel oluşturulan df'den türetiyoruz.
            # Bu, alt bölümün tamamen bağımsız çalışmasını sağlar.
            df_secilen_hafta = df_for_daily_analysis[df_for_daily_analysis['Eğitim Haftası'] == secilen_hafta].copy()

            if not df_secilen_hafta.empty:
                # Buradan sonraki tüm kodlar `df_secilen_hafta` kullandığı için
                # otomatik olarak doğru (tüm egzersizleri içeren) veriyi kullanacaktır.
                st.subheader(f"Hafta {secilen_hafta}: Bir Bakışta Özet")
                weekly_error_summary = df_secilen_hafta.groupby('Oyun Tipi').size().reset_index(name='Hata Sayısı')
                most_errors = weekly_error_summary.loc[weekly_error_summary['Hata Sayısı'].idxmax()]
                least_errors = weekly_error_summary.loc[weekly_error_summary['Hata Sayısı'].idxmin()]

                col1_gunluk, col2_gunluk, col3_gunluk = st.columns(3)
                with col1_gunluk:
                    st.metric("Haftanın Gözdesi 🏃‍♂️", f"{df_secilen_hafta['Oyun Tipi'].mode()[0]}")
                with col2_gunluk:
                    st.metric("Odak Alanı 🎯", f"{most_errors['Oyun Tipi']}")
                with col3_gunluk:
                    st.metric("Haftanın Başarısı ✨", f"{least_errors['Oyun Tipi']}")
                st.divider()

                st.subheader("Haftalık Aktivite ve Hata Dağılımı")
                col_chart1, col_chart2 = st.columns(2)
                with col_chart1:
                    gun_sirasi = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
                    daily_activity = df_secilen_hafta['Haftanın Günü'].value_counts().reindex(gun_sirasi).fillna(0)
                    fig_daily_activity = px.bar(daily_activity, x=daily_activity.index, y=daily_activity.values,
                                                title="Günlük Aktivite Yoğunluğu (Toplam Hata)",
                                                labels={'x': 'Haftanın Günü', 'y': 'Toplam Aktivite Sayısı'},
                                                template="plotly_dark")
                    st.plotly_chart(fig_daily_activity, use_container_width=True)

                with col_chart2:
                    # DEĞİŞİKLİK: Grafik başlığını daha bilgilendirici hale getirdik.
                    pie_title = f"Hafta {secilen_hafta}: Hataların Egzersizlere Göre Dağılımı"
                    fig_pie_errors = px.pie(weekly_error_summary, names='Oyun Tipi', values='Hata Sayısı',
                                            title=pie_title,
                                            template="plotly_dark")
                    st.plotly_chart(fig_pie_errors, use_container_width=True)
                st.divider()

                st.subheader("Egzersiz Bazında Detaylı Raporlar")
                # Kalan tüm raporlama kodları `df_secilen_hafta` üzerinden çalıştığı için
                # herhangi bir değişiklik yapmaya gerek yoktur.
                # ... (Mevcut expander ve karne kodlarınız burada aynı şekilde kalabilir) ...
                calisilan_egzersizler = sorted(df_secilen_hafta['Oyun Tipi'].unique())
                for game in calisilan_egzersizler:
                    with st.expander(f"Raporu Gör: {game}"):
                        # Raporlama kodları... (değişiklik yok)
                        df_game_in_week = df_secilen_hafta[df_secilen_hafta['Oyun Tipi'] == game]
                        total_errors_in_game = len(df_game_in_week)
                        num_sessions = df_game_in_week['datetime'].dt.date.nunique()
                        total_possible_questions = num_sessions * 10
                        success_rate_weekly = ((
                                                           total_possible_questions - total_errors_in_game) / total_possible_questions) * 100 if total_possible_questions > 0 else 0
                        success_rate_weekly = max(0, success_rate_weekly)
                        r_col1, r_col2, r_col3 = st.columns(3)
                        r_col1.metric("Toplam Hata", f"{total_errors_in_game} Hata")
                        r_col2.metric("Çözülme Sayısı (Oturum)", f"{num_sessions} kez")
                        r_col3.metric("Ortalama Başarı", f"%{success_rate_weekly:.0f}")

                if not df_secilen_hafta.empty:
                    st.divider()
                    st.subheader(f"📝 Hafta {secilen_hafta}: Egzersiz Karnesi")
                    # Karne kodları... (değişiklik yok)
                    karne_verileri = []
                    for game in sorted(df_secilen_hafta['Oyun Tipi'].unique()):
                        df_game_in_week = df_secilen_hafta[df_secilen_hafta['Oyun Tipi'] == game]
                        avg_success_rate_game = (1 - (
                                    len(df_game_in_week) / (df_game_in_week['datetime'].dt.date.nunique() * 10))) * 100
                        karne_verileri.append({
                            "Egzersiz Adı": game,
                            "Haftalık Başarı": int(round(avg_success_rate_game)),
                            "Toplam Hata": len(df_game_in_week),
                            "Çözülme Sayısı": df_game_in_week['datetime'].dt.date.nunique(),
                            "En Yoğun Gün": df_game_in_week['Haftanın Günü'].mode()[
                                0] if not df_game_in_week.empty else "N/A"
                        })
                    if karne_verileri:
                        df_karne = pd.DataFrame(karne_verileri)
                        st.dataframe(df_karne, column_config={
                            "Haftalık Başarı": st.column_config.ProgressColumn("Haftalık Başarı", format="%d%%",
                                                                               min_value=0, max_value=100)
                        }, use_container_width=True, hide_index=True)
        else:
            st.info("Günlük detay analizi için seçilen dönemde tamamlanmış bir hafta bulunmamaktadır.")


# --- 5. Hata Yönetimi Bloğu (İkinci Dosyadan) ---
except requests.exceptions.HTTPError as e:
    status_code = e.response.status_code
    st.set_page_config(layout="centered")  # Hata sayfaları için merkezi layout daha iyi durur
    if status_code in [401, 403]:
        st.title("🔒 Erişim Engellendi")
        st.error("Bu öğrencinin gelişim raporunu görüntüleme yetkiniz bulunmamaktadır.")
        st.info(
            "Lütfen kendi öğrenci listenizden bir seçim yaptığınızdan emin olun veya yöneticinizle iletişime geçin.")
        st.image("https://http.cat/403", use_container_width=True)
    elif status_code == 404:
        st.title("🤷‍♂️ Kayıt Bulunamadı")
        st.warning(
            f"Aradığınız veriye ulaşılamadı. Sunucudan gelen mesaj: {e.response.json().get('detail', 'Belirtilmedi')}")
        st.info("Lütfen URL'yi kontrol edin veya bu öğrencinin sisteme kayıtlı olduğundan emin olun.")
        st.image("https://http.cat/404", use_container_width=True)
    else:
        st.title("🚫 Beklenmedik API Hatası")
        st.error(
            f"Veri yüklenirken bir sunucu hatası oluştu. Lütfen daha sonra tekrar deneyin.\n\nDurum Kodu: {status_code}")
        st.code(f"Hata Detayı: {e.response.text}", language="json")

except requests.exceptions.RequestException:
    st.set_page_config(layout="centered")
    st.title("🔌 Bağlantı Hatası")
    st.error(
        "Uygulamanın veri sunucusuna (API) ulaşılamıyor. Lütfen internet bağlantınızı kontrol edin veya sunucunun çalıştığından emin olun.")
    st.image("https://http.cat/503", use_container_width=True)

except ValueError:
    st.set_page_config(layout="centered")
    st.title("❌ Geçersiz İstek")
    st.error("URL'deki öğrenci ID'si geçersiz bir formatta. Lütfen öğretmen panelinden doğru bir şekilde geliniz.")

except Exception as e:
    st.set_page_config(layout="centered")
    st.title("🤔 Beklenmedik Bir Sorun Oluştu")
    st.error(
        "Uygulama çalışırken beklenmedik bir hata meydana geldi. Lütfen sayfayı yenileyin veya daha sonra tekrar deneyin.")
    st.code(f"Teknik Hata Detayı: {e}", language="text")