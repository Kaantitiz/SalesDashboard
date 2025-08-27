#!/bin/bash

echo "🚀 WTC Sales Dashboard Deployment Script"
echo "========================================"

# PostgreSQL bağımlılığını kontrol et
echo "📦 PostgreSQL bağımlılığı kontrol ediliyor..."
if ! python -c "import psycopg2" 2>/dev/null; then
    echo "❌ psycopg2 bulunamadı. Yükleniyor..."
    pip install psycopg2-binary
else
    echo "✅ psycopg2 zaten yüklü"
fi

# Environment variables kontrol et
echo "🔧 Environment variables kontrol ediliyor..."
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL bulunamadı!"
    echo "⚠️  Render'da DATABASE_URL environment variable'ını ayarlayın"
    exit 1
else
    echo "✅ DATABASE_URL bulundu"
fi

# Veritabanı bağlantısını test et
echo "🔌 Veritabanı bağlantısı test ediliyor..."
python -c "
import os
from main import create_app
from models import db

app = create_app()
with app.app_context():
    try:
        db.engine.execute('SELECT 1')
        print('✅ PostgreSQL bağlantısı başarılı')
    except Exception as e:
        print(f'❌ PostgreSQL bağlantı hatası: {e}')
        exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Veritabanı bağlantısı başarısız!"
    exit 1
fi

# Veritabanı tablolarını oluştur
echo "🗄️ Veritabanı tabloları oluşturuluyor..."
python -c "
from main import create_app
from models import db

app = create_app()
with app.app_context():
    db.create_all()
    print('✅ Tablolar oluşturuldu')
"

# Migration scripti varsa çalıştır
if [ -f "migrate_to_postgres.py" ]; then
    echo "🔄 Migration scripti çalıştırılıyor..."
    python migrate_to_postgres.py
fi

# Admin kullanıcısı oluştur
echo "👤 Admin kullanıcısı kontrol ediliyor..."
python -c "
from main import create_app
from models import db, User, UserRole

app = create_app()
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@company.com',
            first_name='Admin',
            last_name='User',
            role=UserRole.ADMIN,
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('✅ Admin kullanıcısı oluşturuldu: admin/admin123')
    else:
        print('👤 Admin kullanıcısı zaten mevcut')
"

echo "🎉 Deployment tamamlandı!"
echo "📊 Artık verileriniz PostgreSQL'de kalıcı olarak saklanacak"
echo "🌐 Uygulama Render'da çalışmaya hazır!"
