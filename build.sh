#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🚀 Build başlıyor..."

echo "📦 Paketler yükleniyor..."
pip install -r requirements.txt
echo "✅ Paketler yüklendi"

echo "🗄️ PostgreSQL migration çalıştırılıyor..."
python postgres_migration.py
echo "✅ PostgreSQL migration tamamlandı"

echo "🎉 Build tamamlandı!"
