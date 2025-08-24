#!/usr/bin/env python3
"""
Manuel kullanıcı oluşturma scripti
Bu script admin kullanıcısını oluşturur
"""

from main import create_app
from models import db, User, UserRole, Department
from werkzeug.security import generate_password_hash

def create_admin_user():
    """Admin kullanıcısını oluştur"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🗄️ Veritabanı tabloları oluşturuluyor...")
            db.create_all()
            print("✅ Tablolar oluşturuldu")
            
            # Admin kullanıcısı oluştur
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
                print("👤 Admin kullanıcısı oluşturuldu: admin/admin123")
            else:
                print("👤 Admin kullanıcısı zaten mevcut")
            
            # Basit departman oluştur
            dept = Department.query.filter_by(name='Genel').first()
            if not dept:
                dept = Department(
                    name='Genel',
                    description='Genel departman'
                )
                db.session.add(dept)
                print("🏢 Genel departman oluşturuldu")
            
            db.session.commit()
            print("🎉 Kullanıcı oluşturma başarılı!")
            
        except Exception as e:
            print(f"❌ Hata: {e}")
            db.session.rollback()
            raise e

if __name__ == '__main__':
    create_admin_user()
