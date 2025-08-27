#!/bin/bash

echo "🚀 WTC Sales Dashboard Build Script"
echo "==================================="

# Python bağımlılıklarını yükle
echo "📦 Python bağımlılıkları yükleniyor..."
pip install -r requirements.txt

# PostgreSQL bağımlılığı requirements.txt'den yükleniyor
echo "🔍 PostgreSQL bağımlılığı kontrol ediliyor..."
python -c "import psycopg2; print('✅ psycopg2 başarıyla yüklendi')" || echo "❌ psycopg2 yüklenemedi"

# Gerekli dizinleri oluştur
echo "📁 Gerekli dizinler oluşturuluyor..."
mkdir -p uploads
mkdir -p instance

echo "🎉 Build tamamlandı!"
