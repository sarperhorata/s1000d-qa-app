#!/bin/bash

# S1000D QA Uygulaması Başlatma Scripti

echo "S1000D QA Uygulaması başlatılıyor..."
BASE_DIR="/Users/sarperhorata/s1000d QA/s1000d-qa-app"

# Backend'i başlat
echo "Backend başlatılıyor..."
cd "$BASE_DIR/backend"
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "Backend başlatıldı (PID: $BACKEND_PID)"
echo "Backend URL: http://localhost:8000"

# 5 saniye bekle - backend'in başlaması için zaman ver
echo "Backend'in başlaması bekleniyor..."
sleep 5

# Backend'in çalışıp çalışmadığını kontrol et
if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo "Backend başarıyla çalışıyor!"
else
    echo "HATA: Backend başlatılamadı. Logları kontrol edin."
    exit 1
fi

# Frontend'i başlat
echo "Frontend başlatılıyor..."
cd "$BASE_DIR/frontend"
npm start &
FRONTEND_PID=$!
echo "Frontend başlatıldı (PID: $FRONTEND_PID)"
echo "Frontend URL: http://localhost:3000"

# Çıkış işlemi için ctrl+c yakalamak
trap "echo 'Kapatılıyor...'; kill $BACKEND_PID; kill $FRONTEND_PID; exit" INT

# Süreçleri bekle
echo "Uygulamalar çalışıyor. Kapatmak için Ctrl+C tuşlarına basın."
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:8000"
wait 