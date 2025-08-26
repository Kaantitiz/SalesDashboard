#!/usr/bin/env python3
"""
Veri Kontrol Script'i
Bu script veritabanındaki verileri kontrol eder ve eksik verileri tespit eder
"""

import os
import sys
from datetime import datetime

def check_database_connection():
    """Veritabanı bağlantısını kontrol eder"""
    try:
        from main import create_app
        from models import db
        
        app = create_app()
        with app.app_context():
            # Veritabanı bağlantısını test et
            db.engine.execute('SELECT 1')
            print("✅ Veritabanı bağlantısı başarılı")
            return True
    except Exception as e:
        print(f"❌ Veritabanı bağlantı hatası: {e}")
        return False

def check_tables():
    """Veritabanı tablolarını kontrol eder"""
    try:
        from main import create_app
        from models import db
        
        app = create_app()
        with app.app_context():
            # Tüm tabloları listele
            tables = db.engine.table_names()
            print(f"📋 Mevcut tablolar: {tables}")
            
            expected_tables = [
                'user', 'department', 'sales', 'returns', 
                'planning', 'target', 'activity_log', 'task', 
                'task_comment', 'notification', 'product'
            ]
            
            missing_tables = [t for t in expected_tables if t not in tables]
            if missing_tables:
                print(f"⚠️ Eksik tablolar: {missing_tables}")
            else:
                print("✅ Tüm tablolar mevcut")
            
            return True
    except Exception as e:
        print(f"❌ Tablo kontrol hatası: {e}")
        return False

def check_data_counts():
    """Veri sayılarını kontrol eder"""
    try:
        from main import create_app
        from models import db, User, Department, Sales, Returns, Planning
        
        app = create_app()
        with app.app_context():
            print("\n📊 Veri Sayıları:")
            
            # Kullanıcı sayısı
            user_count = User.query.count()
            print(f"👥 Kullanıcılar: {user_count}")
            
            # Departman sayısı
            dept_count = Department.query.count()
            print(f"🏢 Departmanlar: {dept_count}")
            
            # Satış sayısı
            sales_count = Sales.query.count()
            print(f"💰 Satışlar: {sales_count}")
            
            # İade sayısı
            returns_count = Returns.query.count()
            print(f"🔄 İadeler: {returns_count}")
            
            # Planlama sayısı
            planning_count = Planning.query.count()
            print(f"📅 Planlamalar: {planning_count}")
            
            return True
    except Exception as e:
        print(f"❌ Veri sayısı kontrol hatası: {e}")
        return False

def check_sample_data():
    """Örnek verileri kontrol eder"""
    try:
        from main import create_app
        from models import db, User, Department, Sales
        
        app = create_app()
        with app.app_context():
            print("\n🔍 Örnek Veriler:")
            
            # İlk kullanıcı
            first_user = User.query.first()
            if first_user:
                print(f"👤 İlk kullanıcı: {first_user.username} ({first_user.get_full_name()})")
            else:
                print("❌ Hiç kullanıcı yok!")
            
            # İlk departman
            first_dept = Department.query.first()
            if first_dept:
                print(f"🏢 İlk departman: {first_dept.name}")
            else:
                print("❌ Hiç departman yok!")
            
            # İlk satış
            first_sale = Sales.query.first()
            if first_sale:
                print(f"💰 İlk satış: {first_sale.customer_name} - {first_sale.total_amount}")
            else:
                print("❌ Hiç satış yok!")
            
            return True
    except Exception as e:
        print(f"❌ Örnek veri kontrol hatası: {e}")
        return False

def check_environment():
    """Environment variables'ları kontrol eder"""
    print("\n🌍 Environment Variables:")
    
    env_vars = [
        'DATABASE_URL', 'FLASK_ENV', 'SECRET_KEY', 
        'JWT_SECRET_KEY', 'PYTHON_VERSION'
    ]
    
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            if 'SECRET' in var or 'KEY' in var:
                print(f"✅ {var}: {'*' * 10}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Tanımlanmamış")
    
    return True

def main():
    """Ana kontrol fonksiyonu"""
    print("🔍 Veri Kontrol Script'i Başlatılıyor...")
    print("=" * 50)
    
    checks = [
        ("Environment Variables", check_environment),
        ("Database Connection", check_database_connection),
        ("Tables", check_tables),
        ("Data Counts", check_data_counts),
        ("Sample Data", check_sample_data)
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"\n🔍 {check_name} kontrol ediliyor...")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} kontrol hatası: {e}")
            results.append((check_name, False))
    
    print("\n" + "=" * 50)
    print("📋 Kontrol Sonuçları:")
    
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for check_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
    
    print(f"\n🎯 Başarı Oranı: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 Tüm kontroller başarılı!")
    else:
        print("⚠️ Bazı kontroller başarısız. Lütfen hataları inceleyin.")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
