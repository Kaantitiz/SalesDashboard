#!/usr/bin/env python3
"""
Basit Veri Kontrol Script'i
Bu script temel veritabanı bağlantısını ve tabloları kontrol eder
"""

import os
import sys

def check_basic_connection():
    """Temel veritabanı bağlantısını kontrol eder"""
    try:
        from main import create_app
        from models import db
        
        app = create_app()
        with app.app_context():
            # Basit bağlantı testi
            result = db.engine.execute('SELECT 1')
            print("✅ Veritabanı bağlantısı başarılı")
            return True
    except Exception as e:
        print(f"❌ Veritabanı bağlantı hatası: {e}")
        return False

def check_tables():
    """Temel tabloları kontrol eder"""
    try:
        from main import create_app
        from models import db
        
        app = create_app()
        with app.app_context():
            # Tabloları listele
            tables = db.engine.table_names()
            print(f"📋 Mevcut tablolar: {tables}")
            
            # Temel tablolar
            basic_tables = ['user', 'department', 'sales', 'returns']
            missing_tables = [t for t in basic_tables if t not in tables]
            
            if missing_tables:
                print(f"⚠️ Eksik tablolar: {missing_tables}")
            else:
                print("✅ Temel tablolar mevcut")
            
            return True
    except Exception as e:
        print(f"❌ Tablo kontrol hatası: {e}")
        return False

def main():
    """Ana kontrol fonksiyonu"""
    print("🔍 Basit Veri Kontrol Script'i Başlatılıyor...")
    print("=" * 50)
    
    checks = [
        ("Basic Database Connection", check_basic_connection),
        ("Tables", check_tables)
    ]
    
    for check_name, check_func in checks:
        print(f"\n🔍 {check_name} kontrol ediliyor...")
        try:
            result = check_func()
            if not result:
                print(f"❌ {check_name} başarısız!")
                return False
        except Exception as e:
            print(f"❌ {check_name} kontrol hatası: {e}")
            return False
    
    print("\n🎉 Tüm kontroller başarılı!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
