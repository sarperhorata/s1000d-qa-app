# S1000D QA System - Docker Kurulum Kılavuzu

## 🚀 Hızlı Başlangıç (Batuhan için)

### Ön Gereksinimler
- Docker Desktop kurulu olmalı
- Docker Compose kurulu olmalı (Docker Desktop ile birlikte gelir)
- En az 8GB RAM
- En az 10GB boş disk alanı

### Adım Adım Kurulum

#### 1. Docker'ın Çalıştığını Kontrol Et
```bash
docker --version
docker-compose --version
```

Çıktı şöyle olmalı:
```
Docker version 24.x.x
Docker Compose version v2.x.x
```

#### 2. Projeyi Klonla / İndir
```bash
cd "/Users/sarperhorata/s1000d QA/s1000d-qa-app"
```

#### 3. PDF Dosyasının Yerini Kontrol Et
PDF dosyası şu konumda olmalı:
```
/Users/sarperhorata/s1000d QA/S1000D Issue 6/Specification/S1000D Issue 6.PDF
```

Eğer başka yerdeyse, `docker-compose.yml` dosyasındaki volume path'i güncelle:
```yaml
volumes:
  - /SENIN/PDF/YOLUN:/app/data/S1000D_Issue_6.PDF:ro
```

#### 4. Docker Container'ları Başlat
```bash
# İlk kez çalıştırıyorsan (build gerekli)
docker-compose up --build

# Sonraki çalıştırmalarda
docker-compose up

# Arka planda çalıştırmak için
docker-compose up -d
```

#### 5. Sistemin Hazır Olmasını Bekle
Container'lar başladıktan sonra:
- Backend hazır: ~30-40 saniye
- Frontend hazır: ~10-20 saniye

#### 6. Uygulamayı Aç
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000

#### 7. İlk İndexleme (Sadece İlk Kez)
Container içine gir ve indexleme başlat:
```bash
# Backend container'a gir
docker exec -it s1000d-qa-backend bash

# İndexleme başlat (10-15 dakika)
python document_indexer.py --no-ocr

# Container'dan çık
exit
```

## 🔧 Sık Karşılaşılan Hatalar ve Çözümleri

### Hata 1: "Port already in use"
**Sebep**: 8000 veya 3000 portu kullanımda

**Çözüm**:
```bash
# Kullanılan portları kontrol et
lsof -i :8000
lsof -i :3000

# Process'i öldür
kill -9 <PID>

# VEYA docker-compose.yml'de port değiştir
ports:
  - "8001:8000"  # 8000 yerine 8001
```

### Hata 2: "Cannot find PDF file"
**Sebep**: PDF dosyası volume'da yok

**Çözüm**:
```bash
# PDF yolunu kontrol et
ls -la "/Users/sarperhorata/s1000d QA/S1000D Issue 6/Specification/S1000D Issue 6.PDF"

# docker-compose.yml'de doğru yolu ayarla
```

### Hata 3: "Import errors" veya "Module not found"
**Sebep**: Python paketleri eksik

**Çözüm**:
```bash
# Container'ı rebuild et
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Hata 4: "ChromaDB connection error"
**Sebep**: Persistent volume sorunu

**Çözüm**:
```bash
# Volume'ları temizle ve yeniden başlat
docker-compose down -v
docker-compose up --build
```

### Hata 5: "Health check failed"
**Sebep**: Backend başlamadı veya yavaş başladı

**Çözüm**:
```bash
# Logları kontrol et
docker-compose logs backend

# Manuel health check
docker exec s1000d-qa-backend curl http://localhost:8000/health
```

## 📊 Container Yönetimi

### Container Durumunu Kontrol Et
```bash
# Çalışan container'ları gör
docker-compose ps

# Detaylı durum
docker ps
```

### Logları İzle
```bash
# Tüm loglar
docker-compose logs -f

# Sadece backend
docker-compose logs -f backend

# Sadece frontend  
docker-compose logs -f frontend

# Son 100 satır
docker-compose logs --tail=100 backend
```

### Container'ları Durdur
```bash
# Nazikçe durdur
docker-compose stop

# Tamamen kaldır
docker-compose down

# Volume'larla birlikte kaldır (VERİ SİLİNİR!)
docker-compose down -v
```

### Container'ları Yeniden Başlat
```bash
# Hepsini yeniden başlat
docker-compose restart

# Sadece backend'i yeniden başlat
docker-compose restart backend
```

## 🔍 Debug ve Test

### Backend Container'a Gir
```bash
docker exec -it s1000d-qa-backend bash
```

Container içinde:
```bash
# Python çalışıyor mu?
python --version

# Test script çalıştır
python test_enhanced_system.py

# ChromaDB kontrol et
ls -la chroma_data/

# Logs kontrol et
tail -f logs/app.log
```

### API'yi Test Et
```bash
# Health check
curl http://localhost:8000/health

# Index status
curl http://localhost:8000/index-status

# Test query
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is S1000D?", "page_size": 3}'
```

## 💾 Veri Yönetimi

### Backup Oluştur
```bash
# Container içinde
docker exec s1000d-qa-backend /app/backend/backup_chromadb.sh

# VEYA host'tan
docker-compose exec backend bash -c "cd /app/backend && ./backup_chromadb.sh"
```

### Backup'ı Geri Yükle
```bash
# Container'a gir
docker exec -it s1000d-qa-backend bash

# Backup'ı restore et
cp -r backups/chromadb_YYYYMMDD_HHMMSS chroma_data
```

### Persistent Data Yeri
```bash
# Host makinede data burada:
./backend/chroma_data/  # ChromaDB index
./backend/logs/         # Log dosyaları
./backend/backups/      # Backup'lar
```

## ⚙️ Yapılandırma

### Environment Variables
`docker-compose.yml` dosyasında değiştir:

```yaml
environment:
  - DEBUG=true                    # Debug modunu aç
  - OCR_ENABLED=false            # OCR'ı kapat (daha hızlı)
  - CHUNK_SIZE=1500              # Chunk boyutunu değiştir
  - BATCH_SIZE=50                # Batch size'ı küçült (bellek tasarrufu)
```

### Resource Limits
Bellek sınırı ekle:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          memory: 2G
```

## 🚀 Production Deployment

### Optimize Edilmiş Build
```bash
# Production build
docker-compose -f docker-compose.prod.yml up --build -d
```

### Multi-stage Build Kullan
```bash
# Azure için optimize edilmiş
docker build -f Dockerfile.azure -t s1000d-qa:latest .
```

## 📈 Performance İyileştirme

### 1. Layer Caching
```dockerfile
# requirements.txt önce kopyala (cache için)
COPY backend/requirements.txt ./backend/
RUN pip install -r backend/requirements.txt
# Sonra kodu kopyala
COPY backend/ ./backend/
```

### 2. Multi-stage Build
```dockerfile
# Build ve runtime'ı ayır
FROM python:3.11-slim as builder
# ... build işlemleri ...

FROM python:3.11-slim as runtime
COPY --from=builder /app /app
```

### 3. Docker Compose Override
Geliştirme için:
```bash
# docker-compose.override.yml oluştur
version: '3.8'
services:
  backend:
    volumes:
      - ./backend:/app/backend  # Live reload için
    environment:
      - DEBUG=true
```

## 🆘 Yardım ve Destek

### Yararlı Komutlar
```bash
# Tüm Docker resource'ları temizle
docker system prune -a

# Volume'ları temizle
docker volume prune

# Build cache'i temizle
docker builder prune

# Container'ların resource kullanımını gör
docker stats

# Disk kullanımını kontrol et
docker system df
```

### Log Seviyeleri
Container başlatırken:
```bash
# Verbose logging
docker-compose up --build

# Quiet mode
docker-compose up -d

# Detaylı build logs
docker-compose build --progress=plain
```

## ✅ Başarı Kontrol Listesi

Batuhan için son kontroller:

- [ ] Docker Desktop çalışıyor
- [ ] PDF dosyası erişilebilir
- [ ] `docker-compose up` hatasız çalıştı
- [ ] Backend health check: http://localhost:8000/health → `{"status": "ok"}`
- [ ] Frontend açılıyor: http://localhost:3000
- [ ] İlk indexleme tamamlandı
- [ ] Test sorgusu çalışıyor

## 🎯 Hızlı Komut Referansı

```bash
# Başlat
docker-compose up -d

# Durdur
docker-compose stop

# Logları gör
docker-compose logs -f backend

# Health check
curl http://localhost:8000/health

# Yeniden başlat
docker-compose restart

# Temizle ve yeniden başlat
docker-compose down && docker-compose up --build

# Container'a gir
docker exec -it s1000d-qa-backend bash

# Backup al
docker-compose exec backend ./backup_chromadb.sh
```

---

**Son Güncelleme**: 17 Ekim 2025  
**Versiyon**: v2.0  
**Durum**: Production Ready ✅

Sorularınız için DOCKER_GUIDE.md dosyasına bakın veya container loglarını inceleyin.

