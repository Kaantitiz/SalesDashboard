#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🚀 Build başlıyor..."

echo "📦 Paketler yükleniyor..."
pip install -r requirements.txt
echo "✅ Paketler yüklendi"

echo "🗄️ Veritabanı oluşturuluyor..."
python simple_db.py
echo "✅ Veritabanı oluşturuldu"

echo "🎉 Build tamamlandı!"
