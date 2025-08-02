
![letstep](https://github.com/user-attachments/assets/da3f7c21-645b-4a9b-8bbe-2b8dff560562)


🎯 Proje Amacı

LetStep, bireylerin dijital, zihinsel ve sosyal gelişimlerini desteklemek için geliştirilmiştir.

🧩 Uygulama içerisinde:

--   🔤 Okuma & yazma egzersizleri

--   🧠 Dikkat, hafıza ve eşleştirme oyunları

--   🎧 Sesli içerik (Whisper & ffmpeg entegrasyonu)

--   👨‍👩‍👧‍👦 Ebeveyn & öğretmen içerik paylaşımı 

--   📊 Streamlit + Plotly ile görsel analizler

👥 Hedef Kitle

--   👶 Öğrenciler

--   👩‍🏫 Öğretmenler

--   👨‍👩‍👧‍👦 Aileler

Nöroçeşitliliğe sahip bireyler ve onlara destek olan herkes için.



🧩 Teknoloji Yığını

--   📦 Backend     : FastAPI, SQLAlchemy, Alembic

--   🗃️ Veritabanı  : SQLite

--   🎨 Frontend    : HTML, CSS, JavaScript (vanilla)

--   🔐 Kimlik      : JWT, Passlib, Bcrypt, OAuth

--   📤 E-posta     : FastAPI-Mail

--   🧠 AI Ses İşleme : openai-whisper, ffmpeg, pydub

--   📊 Görselleştirme: Streamlit, Plotly, Pandas


⚙️ Gereksinimler

--   ✅ Python 3.11+

--   ✅ ffmpeg (media işlemleri için) (https://ffmpeg.org/download.html)

--   🔗 Windows & Ubuntu / Debian  & macOS lütfen işletim sisteminize uygun ffmpeg paketini kurunuz.



🚀 Kurulum Adımları

# 1. Reposu klonla
--   git clone https://github.com/Anonyuser-x/letstep.git
--   cd letstep

# 2. Sanal ortam oluştur
--   python -m venv .venv

# Windows:
--   .venv\Scripts\activate

# Linux/macOS:
--   source .venv/bin/activate

# 3. Gereksinimleri yükle
--   pip install -r requirements.txt

--   ffmpeg paketini yüklediğinizi ve ana klasör içerisinde tuttuğunuzdan emin olun

# 4. Ortam dosyasını oluştur
--   cp .config.env.example .config.env
--   # .config.env içeriğini kendine göre düzenle

# 5. Uygulamayı başlat
--   uvicorn main:app --reload

📁 Dosya Yapısı

📁 alembic/             # Gerekli migrationlar ve veritabanı güncellemeleri
📁 app/                 # FastAPI backend (main.py, routers, db vb.)
📁 ffmpeg/              # Ses işlemesi için gerekli yazılım 
📁 static/              # CSS, JS dosyaları
📁 templates/           # HTML sayfaları (Jinja2)
📄 database.db          # Veritabanı (örnek içeriklerle birlikte)
📄 requirements.txt     # Bağımlılık listesi
📄 .env                 # Ortam değişkenleri (kişisel - gitignore'da)
📄 .config.env.example  # Örnek ortam dosyası (repoya dahil)
📄 README.md            # Proje açıklaması


📈 Veri Görselleştirme & Analiz

LetStep, eğitimciler ve aileler için bireysel gelişim takibi sunar:

--   📊 Streamlit paneli ile gelişim grafikleri

--   📌 Plotly ile interaktif analizler

--   📑 Pandas ile veritabanı işleme yeteneği

--   🤝 Katkı & İletişim

Bu proje bir bootcamp projesi kapsamında sosyal fayda amacıyla geliştirilmiştir.

--   👤 Geliştirici: Letstep Proje Ekibi
--   ▶️YouTube🔴 https://www.youtube.com/@LetStep69

