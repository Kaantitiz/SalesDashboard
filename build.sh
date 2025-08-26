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
        
        # Veritabanı tablolarını kontrol et
        echo "Veritabani tablolari kontrol ediliyor..."
        python -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE table_schema = \\'public\\';')
    tables = cursor.fetchall()
    print('✅ Mevcut tablolar:', [t[0] for t in tables])
    
    # Kullanıcı sayısını kontrol et
    cursor.execute('SELECT COUNT(*) FROM \"user\"')
    user_count = cursor.fetchone()[0]
    print('✅ Kullanici sayisi:', user_count)
    
    conn.close()
except Exception as e:
    print('❌ Veritabani kontrol hatasi:', e)
"
        
        # Veri kontrol script'ini çalıştır
        echo "Veri kontrol script'i calistiriliyor..."
        python check_data.py
        
    else
        echo "⚠️ PostgreSQL migration hatasi, tekrar deneniyor..."
        
        # İkinci deneme
        echo "Ikinci migration denemesi..."
        python postgres_migration.py
        
        if [ $? -eq 0 ]; then
            echo "✅ Ikinci denemede migration basarili!"
            # Veri kontrol
            python check_data.py
        else
            echo "❌ Migration basarisiz, SQLite ile devam ediliyor..."
            python -c "
from main import create_app
from models import db
app = create_app()
with app.app_context():
    db.create_all()
    print('SQLite veritabani tablolari olusturuldu')
"
        fi
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
