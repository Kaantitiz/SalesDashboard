#!/bin/bash

echo "🚀 WTC Sales Dashboard Build Script"
echo "==================================="

# Python bağımlılıklarını yükle
echo "📦 Python bağımlılıkları yükleniyor..."
pip install -r requirements.txt

# PostgreSQL bağımlılığı requirements.txt'den yükleniyor
echo "🔍 PostgreSQL bağımlılığı kontrol ediliyor..."
python -c "import psycopg2; print('✅ psycopg2 başarıyla yüklendi')" 2>/dev/null || \
python -c "import psycopg2_binary; print('✅ psycopg2-binary başarıyla yüklendi')" 2>/dev/null || \
python -c "import pg8000; print('✅ pg8000 başarıyla yüklendi')" 2>/dev/null || \
echo "❌ PostgreSQL driver bulunamadı"

# Gerekli dizinleri oluştur
echo "📁 Gerekli dizinler oluşturuluyor..."
mkdir -p uploads
mkdir -p instance

echo "🎉 Build tamamlandı!"
