#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🚀 Build başlıyor..."

echo "📦 Paketler yükleniyor..."
pip install -r requirements.txt
echo "✅ Paketler yüklendi"

echo "🗄️ SQLite veritabanı oluşturuluyor..."
python simple_db.py
echo "✅ SQLite veritabanı oluşturuldu"

echo "🎉 Build tamamlandı!"
