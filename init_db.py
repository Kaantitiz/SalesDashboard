#!/usr/bin/env python3
"""
Veritabanı başlatma ve admin kullanıcısı oluşturma
"""

import os
import sys

def init_database():
    """Veritabanını başlat ve admin kullanıcısı oluştur"""
    try:
        print("🚀 Veritabanı başlatılıyor...")
        
        # Flask app'i import et
        from main import create_app
        from models import db, User, UserRole, Department
        
        app = create_app()
        
        with app.app_context():
            print("🗄️ Tablolar oluşturuluyor...")
            db.create_all()
            print("✅ Tablolar oluşturuldu")
            
            # Admin kullanıcısını kontrol et
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                print("👤 Admin kullanıcısı oluşturuluyor...")
                
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
                
                # Basit departman oluştur
                dept = Department(
                    name='Genel',
                    description='Genel departman'
                )
                db.session.add(dept)
                
                db.session.commit()
                print("🎉 Admin kullanıcısı oluşturuldu: admin/admin123")
            else:
                print("👤 Admin kullanıcısı zaten mevcut")
            
            print("🎯 Veritabanı hazır!")
            
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    init_database()
