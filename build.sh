#!/usr/bin/env bash

echo "Sales Dashboard Deploy Baslatiyor..."

# Python sürümünü kontrol et
python --version

# Gerekli paketleri yükle
echo "Gerekli paketler yukleniyor..."
pip install -r requirements.txt

# Veritabanı migration'larını çalıştır
echo "Veritabani migration'lari calistiriliyor..."
python -c "
from main import create_app
from models import db
app = create_app()
with app.app_context():
    db.create_all()
    print('Veritabani tablolari olusturuldu')
"

# Test çalıştır
echo "Test calistiriliyor..."
python -c "
from main import create_app
app = create_app()
print('Uygulama basariyla olusturuldu')
"

echo "Build tamamlandi! Deploy icin hazir."
