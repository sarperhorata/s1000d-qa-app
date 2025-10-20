#!/bin/bash
# S1000D QA System - Docker Quick Start Script
# Batuhan için kolay başlatma scripti

set -e

echo "🚀 S1000D QA System - Docker Başlatılıyor..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker çalışmıyor! Lütfen Docker Desktop'ı başlatın."
    exit 1
fi

echo "✅ Docker çalışıyor"
echo ""

# Check if PDF exists
PDF_PATH="/Users/sarperhorata/s1000d QA/S1000D Issue 6/Specification/S1000D Issue 6.PDF"
if [ ! -f "$PDF_PATH" ]; then
    echo "⚠️  Uyarı: PDF dosyası bulunamadı: $PDF_PATH"
    echo "   docker-compose.yml'de PDF yolunu kontrol edin"
    echo ""
fi

# Stop any existing containers
echo "🛑 Eski container'ları durduruluyor..."
docker-compose down 2>/dev/null || true

# Build and start
echo ""
echo "🔨 Container'lar build ediliyor..."
docker-compose build --no-cache

echo ""
echo "🚀 Container'lar başlatılıyor..."
docker-compose up -d

echo ""
echo "⏳ Backend'in hazır olması bekleniyor (30-40 saniye)..."
sleep 10

# Wait for backend to be healthy
MAX_ATTEMPTS=20
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend hazır!"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    echo "   Deneme $ATTEMPT/$MAX_ATTEMPTS..."
    sleep 2
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "❌ Backend başlatılamadı. Logları kontrol edin:"
    echo "   docker-compose logs backend"
    exit 1
fi

echo ""
echo "✅ Frontend hazır olmalı (biraz daha bekleyin)..."
sleep 5

echo ""
echo "════════════════════════════════════════════════════════"
echo "🎉 S1000D QA System Hazır!"
echo "════════════════════════════════════════════════════════"
echo ""
echo "📊 Erişim Linkleri:"
echo "   🔹 API:          http://localhost:8000"
echo "   🔹 API Docs:     http://localhost:8000/docs"
echo "   🔹 Frontend:     http://localhost:3000"
echo ""
echo "📝 İLK KEZ ÇALIŞTIRIYORSAN:"
echo "   1. Backend container'a gir:"
echo "      docker exec -it s1000d-qa-backend bash"
echo "   2. İndexleme başlat (10-15 dakika):"
echo "      python document_indexer.py --no-ocr"
echo "   3. Çıkış yap:"
echo "      exit"
echo ""
echo "🔍 Logları izlemek için:"
echo "   docker-compose logs -f backend"
echo ""
echo "🛑 Durdurmak için:"
echo "   docker-compose stop"
echo ""
echo "════════════════════════════════════════════════════════"

