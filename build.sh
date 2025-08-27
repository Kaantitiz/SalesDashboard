#!/bin/bash

echo "🚀 WTC Sales Dashboard Build Script"
echo "==================================="

# Python bağımlılıklarını yükle
echo "📦 Python bağımlılıkları yükleniyor..."
pip install -r requirements.txt

# PostgreSQL bağımlılığını kontrol et
echo "🔍 PostgreSQL bağımlılığı kontrol ediliyor..."
if ! python -c "import psycopg2" 2>/dev/null; then
    echo "❌ psycopg2 bulunamadı. Yükleniyor..."
    pip install psycopg2-binary
else
    echo "✅ psycopg2 zaten yüklü"
fi

# Gerekli dizinleri oluştur
echo "📁 Gerekli dizinler oluşturuluyor..."
mkdir -p uploads
mkdir -p instance

echo "🎉 Build tamamlandı!"
