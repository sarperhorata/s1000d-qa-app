#!/bin/bash
# Batuhan için basitleştirilmiş başlatma scripti
# Minimal dependencies, kolay anlaşılır

echo "🚀 S1000D QA - Basit Versiyon Başlatılıyor..."
echo ""

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker çalışmıyor! Docker Desktop'ı başlat."
    exit 1
fi

echo "✅ Docker çalışıyor"

# Stop old containers
echo "🛑 Eski container'lar durduruluyor..."
docker-compose -f docker-compose.simple.yml down 2>/dev/null || true

# Build
echo "🔨 Container build ediliyor (basit versiyon)..."
docker-compose -f docker-compose.simple.yml build

# Start
echo "🚀 Container'lar başlatılıyor..."
docker-compose -f docker-compose.simple.yml up -d

echo ""
echo "⏳ Backend hazır oluyor (20-30 saniye)..."
sleep 10

# Wait for health
for i in {1..15}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend hazır!"
        break
    fi
    echo "   Deneme $i/15..."
    sleep 2
done

echo ""
echo "════════════════════════════════════════════════════"
echo "🎉 Basit S1000D QA Sistemi Hazır!"
echo "════════════════════════════════════════════════════"
echo ""
echo "📊 Erişim:"
echo "   API:      http://localhost:8000"
echo "   Docs:     http://localhost:8000/docs"
echo "   Frontend: http://localhost:3000"
echo ""
echo "📝 Özellikler:"
echo "   ✅ TF-IDF based search (basit, hızlı)"
echo "   ✅ XML-first approach"
echo "   ✅ PDF fallback"
echo "   ✅ Minimal dependencies (6 paket)"
echo ""
echo "🔍 Test et:"
echo "   curl http://localhost:8000/health"
echo "   curl http://localhost:8000/stats"
echo ""
echo "🛑 Durdur:"
echo "   docker-compose -f docker-compose.simple.yml down"
echo ""
echo "════════════════════════════════════════════════════"

