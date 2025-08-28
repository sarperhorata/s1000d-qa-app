# 🚀 S1000D QA Application

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/React-18+-61dafb.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)

> **AI-Powered S1000D Documentation Search & Analysis Tool**

Bu uygulama, S1000D teknik dokümantasyon standardını derinlemesine analiz etmek ve sorgulamak için geliştirilmiş **yapay zeka destekli** bir arama ve analiz aracıdır. 3670+ sayfalık büyük PDF dokümanlarını otomatik olarak indexler ve hem metin hem de görsel içerikleri akıllı bir şekilde analiz eder.

## 🎯 Proje Amacı

S1000D dokümantasyonunda spesifik bilgilere hızlı ve doğru şekilde ulaşmak, teknik diyagramları otomatik olarak tanımak ve çoklu format desteği sağlamak için geliştirilmiştir.

## ✨ Özellikler

- 🎯 **Akıllı PDF Indexleme**: 3670+ sayfalık S1000D dokümanlarını otomatik indexler
- 🔍 **Semantik Arama**: Metin tabanlı sorgular için derin öğrenme destekli arama
- 📄 **XML İçerik Desteği**: XML dosyalarında özel parsing ve görüntüleme
- 🌍 **Çoklu Dil Desteği**: Otomatik İngilizce ↔ Türkçe çeviri
- 📍 **Sayfa Referansları**: Sonuçların orijinal sayfa numaralarıyla gösterimi
- 🎨 **Multimodal Görsel Desteği**: PDF'deki diyagram ve görselleri otomatik çıkarır
- 🖼️ **Görsel Arama**: Sorguya göre ilgili görselleri gösterir
- 🤖 **Yerel AI**: Ollama + Llama 3.2 (ücretsiz, gizli)
- 🎭 **Multimodal Analiz**: LLaVA ile görsel analiz ve tanıma
- ⚡ **OpenAI Fallback**: Üretim ortamında OpenAI API desteği
- 🔄 **PDF Yönetimi**: Kolay PDF güncelleme ve yeniden indexleme
- 🐳 **Docker + Render**: Bulut deployment hazır
- 📊 **İleri Düzey Analitik**: Detaylı sorgu istatistikleri ve performans metrikleri

## Kurulum

### Gereksinimler

- Python 3.11+
- Node.js 18+
- npm
- Ollama (yerel LLM için)

### Yerel Kurulum

#### Backend Kurulumu

```bash
cd s1000d-qa-app/backend
pip install -r requirements.txt
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

#### Frontend Kurulumu

```bash
cd s1000d-qa-app/frontend
npm install
npm start
```

### Docker ile Kurulum

```bash
docker build -t s1000d-qa .
docker run -p 8000:8000 s1000d-qa
```

## Kullanım

1. Tarayıcınızda `http://localhost:3000` adresine gidin
2. Sorgunuzu veya XML içeriğini arama kutusuna yazın
3. Çeviri seçeneğini açın veya kapatın
4. "Ara" butonuna tıklayın
5. Dönen sonuçları inceleyin - Her sonuç gizlenebilir/gösterilebilir formatta sunulacaktır
6. Her bir sonuç için orijinal (İngilizce) veya Türkçe çeviri seçenekleri arasında geçiş yapabilirsiniz
7. XML içerikleri için özel formatlı görüntüleme seçeneği bulunmaktadır

### PDF Yönetim Endpoint'leri

Sistem, büyük S1000D PDF dosyalarını yönetmek için aşağıdaki API endpoint'lerini sağlar:

#### PDF Durum Kontrolü
```bash
GET /index-status
```
PDF dosyasının varlığı, boyutu, sayfa sayısı ve index durumunu kontrol eder.

#### PDF Yeniden Indexleme
```bash
POST /reindex-pdf
```
PDF dosyasını yeniden indexler. Yeni spesifikasyon sürümleri için kullanışlıdır.

#### PDF Yol Güncelleme
```bash
POST /update-pdf-path
Content-Type: application/json

{
  "pdf_path": "/path/to/new/specification.pdf"
}
```
Yeni PDF dosyası için yolu günceller.

### Görsel Arama Endpoint'i

```bash
# Sorguya göre ilgili görselleri getir
GET /get-images-for-query?query=business%20rules&limit=5

# Cevap örneği:
{
  "status": "success",
  "query": "business rules",
  "images": [
    {
      "page": 211,
      "index": 0,
      "format": "png",
      "data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
      "size": 15432
    }
  ],
  "total_images": 1
}
```

### Örnek Kullanım

```bash
# Sistem durumunu kontrol et
curl http://localhost:8000/health

# PDF index durumunu kontrol et
curl http://localhost:8000/index-status

# PDF'yi yeniden indexle
curl -X POST http://localhost:8000/reindex-pdf

# AI destekli soru sor
curl -X POST http://localhost:8000/ai-query \
  -H "Content-Type: application/json" \
  -d '{"query": "S1000D Issue 6 nedir?", "language": "tr"}'

# Görsel arama
curl "http://localhost:8000/get-images-for-query?query=aspect%20core&limit=3"
```

### Render Deployment

#### 1. Repository'yi GitHub'a yükleyin

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/s1000d-qa-app.git
git push -u origin main
```

#### 2. Render'da Web Service oluşturun

1. [Render Dashboard](https://dashboard.render.com)'a gidin
2. "New" → "Web Service" seçin
3. GitHub repository'nizi bağlayın
4. Aşağıdaki ayarları yapın:

**Service Settings:**
- **Name:** s1000d-qa-api
- **Runtime:** Docker
- **Build Command:** (boş bırakın - Dockerfile kullanacak)
- **Start Command:** python -m uvicorn backend.app:app --host 0.0.0.0 --port $PORT

**Environment Variables:**
- `OPENAI_API_KEY`: Your OpenAI API key
- `PYTHONPATH`: /app

#### 3. Static Site oluşturun (Frontend için)

1. "New" → "Static Site" seçin
2. GitHub repository'nizi bağlayın
3. Aşağıdaki ayarları yapın:

**Site Settings:**
- **Name:** s1000d-qa-frontend
- **Build Command:** cd frontend && npm install && npm run build
- **Publish Directory:** frontend/build

**Environment Variables:**
- `REACT_APP_API_URL`: Backend service URL (örn: https://s1000d-qa-api.onrender.com)

## API Kullanımı

Backend API'si aşağıdaki endpoint'leri sunar:

### Temel Endpoint'ler

- `GET /health`: API durumunu kontrol etmek için kullanılır
- `POST /initialize-models`: Modelleri manuel olarak initialize eder
- `GET /test-models`: Model test sonuçlarını gösterir

### Sorgu Endpoint'leri

- `POST /ai-query`: AI destekli sorgulama
  - Parametreler:
    - `query`: Sorgu metni
    - `translate`: İngilizce-Türkçe çeviri (boolean, opsiyonel)

- `POST /query`: Klasik sorgulama
  - Parametreler:
    - `query`: Sorgu metni
    - `translate`: Çeviri seçeneği

### Multimodal (Görsel) Endpoint'ler

- `GET /get-images-for-query`: **Yeni!** Sorguya göre ilgili görselleri getirir
  - Parametreler:
    - `query`: Arama sorgusu (örn: "business rules", "aspect core")
    - `limit`: Maksimum görsel sayısı (varsayılan: 5)

- `POST /analyze-image`: Tek bir görseli analiz eder
  - Parametreler:
    - `file`: Yüklenen görsel dosyası
    - `query`: Analiz sorgusu

- `GET /get-pdf-images`: PDF'deki tüm görselleri listeler
- `POST /process-pdf-images`: PDF görsellerini toplu işler

### Detaylı Kullanım Örnekleri

#### Temel İşlemler
```bash
# Sistem durumunu kontrol et
curl http://localhost:8000/health

# PDF index durumunu kontrol et
curl http://localhost:8000/index-status

# PDF'yi yeniden indexle
curl -X POST http://localhost:8000/reindex-pdf
```

#### AI Destekli Sorgulama
```bash
# Türkçe sorgu
curl -X POST http://localhost:8000/ai-query \
  -H "Content-Type: application/json" \
  -d '{"query": "S1000D data module nasıl tanımlanır?", "language": "tr"}'

# Teknik spesifikasyon sorusu
curl -X POST http://localhost:8000/ai-query \
  -H "Content-Type: application/json" \
  -d '{"query": "Business rules kategorileri nelerdir?", "language": "tr"}'
```

#### Görsel Arama (Multimodal)
```bash
# Business rules ile ilgili görselleri ara
curl "http://localhost:8000/get-images-for-query?query=business%20rules&limit=3"

# Aspect core diyagramlarını ara
curl "http://localhost:8000/get-images-for-query?query=aspect%20core&limit=5"

# Data module diyagramlarını ara
curl "http://localhost:8000/get-images-for-query?query=data%20module&limit=3"
```

#### Production Kullanımı (Render)
```bash
# Health check (production)
curl https://your-app.onrender.com/health

# AI sorgu (production)
curl -X POST https://your-app.onrender.com/ai-query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is S1000D?", "language": "en"}'
```

## 🚀 Hızlı Başlangıç

### Demo Kullanımı

1. **Repository'yi klonlayın:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/s1000d-qa-app.git
   cd s1000d-qa-app
   ```

2. **Hızlı kurulum:**
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt
   python -m uvicorn app:app --host 0.0.0.0 --port 8000

   # Frontend (yeni terminal)
   cd ../frontend
   npm install
   npm start
   ```

3. **Test edin:**
   - Tarayıcı: `http://localhost:3000`
   - API Docs: `http://localhost:8000/docs`

## 🤝 Katkıda Bulunma

Bu projeye katkıda bulunmak için:

1. Fork edin 🍴
2. Feature branch oluşturun: `git checkout -b feature/amazing-feature`
3. Commit edin: `git commit -m 'Add amazing feature'`
4. Push edin: `git push origin feature/amazing-feature`
5. Pull Request açın 📝

### Geliştirme Alanı

- 🔧 **Backend geliştirme**: `backend/` klasöründe
- 🎨 **Frontend geliştirme**: `frontend/` klasöründe
- 📚 **Dokümantasyon**: `README.md` ve `docs/` klasöründe

## 🐛 Sorun Bildirimi

Herhangi bir sorunla karşılaştığınızda:

1. [GitHub Issues](https://github.com/YOUR_USERNAME/s1000d-qa-app/issues) sayfasını kullanın
2. Sorun başlığında `[BUG]`, `[FEATURE]`, `[QUESTION]` etiketlerini kullanın
3. Aşağıdaki bilgileri ekleyin:
   - İşletim sistemi ve versiyon
   - Python/Node.js versiyonları
   - Sorun adımları ve beklenen davranış
   - Hata logları (varsa)

## 📊 Teknik Detaylar

### Sistem Gereksinimleri

- **CPU**: 4+ çekirdek önerilir
- **RAM**: 8GB+ önerilir
- **Disk**: 2GB+ boş alan
- **Network**: Stabil internet bağlantısı

### Performance Metrikleri

- **PDF Index Süresi**: ~15-30 dakika (3670 sayfa için)
- **Arama Süresi**: < 2 saniye
- **Bellek Kullanımı**: ~2-4GB (çalışma sırasında)

### AI Modelleri

- **Text Generation**: Llama 3.2 (3B parameters)
- **Embeddings**: SentenceTransformers (all-MiniLM-L6-v2)
- **Vision Analysis**: LLaVA (7B parameters)

## 📞 İletişim

- **Proje Sahibi**: [YOUR_NAME]
- **Email**: [YOUR_EMAIL]
- **LinkedIn**: [YOUR_LINKEDIN]
- **GitHub**: [YOUR_GITHUB]

## 🙏 Teşekkürler

Bu proje aşağıdaki açık kaynaklı projelere dayanmaktadır:

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://reactjs.org/) - Kullanıcı arayüzü kütüphanesi
- [LangChain](https://langchain.com/) - LLM uygulama framework'ü
- [SentenceTransformers](https://sbert.net/) - Embedding modelleri
- [Ollama](https://ollama.ai/) - Yerel LLM çalıştırma

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

<div align="center">
  <strong>S1000D QA Application</strong> - AI-Powered Technical Documentation Search
  <br>
  <sub>Yapay zeka ile güçlendirilmiş teknik dokümantasyon arama aracı</sub>
</div> 