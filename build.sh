#!/usr/bin/env bash

echo "Sales Dashboard Deploy Baslatiyor..."

# Python sürümünü kontrol et
python --version

# Gerekli paketleri yükle
echo "Gerekli paketler yukleniyor..."
pip install -r requirements.txt

# Kalıcı depolama klasörünü oluştur
echo "Kalici depolama klasoru olusturuluyor..."
mkdir -p /opt/render/project/src/uploads
mkdir -p uploads

# PostgreSQL migration'ı çalıştır
echo "PostgreSQL migration calistiriliyor..."
if [ -n "$DATABASE_URL" ]; then
    echo "PostgreSQL veritabani bulundu, migration baslatiliyor..."
    
    # Migration script'ini çalıştır
    echo "Migration script calistiriliyor..."
    python postgres_migration.py
    
    # Migration başarılı mı kontrol et
    if [ $? -eq 0 ]; then
        echo "✅ PostgreSQL migration basarili!"
        
        # Basit veri kontrol
        echo "Basit veri kontrol calistiriliyor..."
        python simple_check.py
        
    else
        echo "⚠️ PostgreSQL migration hatasi, SQLite ile devam ediliyor..."
        python -c "
from main import create_app
from models import db
app = create_app()
with app.app_context():
    db.create_all()
    print('SQLite veritabani tablolari olusturuldu')
"
    fi
else
    echo "DATABASE_URL bulunamadi, SQLite kullaniliyor..."
    python -c "
from main import create_app
from models import db
app = create_app()
with app.app_context():
    db.create_all()
    print('SQLite veritabani tablolari olusturuldu')
"
fi

# Test çalıştır
echo "Test calistiriliyor..."
python -c "
from main import create_app
app = create_app()
print('Uygulama basariyla olusturuldu')
"

echo "Build tamamlandi! Deploy icin hazir."
