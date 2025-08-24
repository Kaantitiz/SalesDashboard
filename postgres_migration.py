#!/usr/bin/env python3
"""
PostgreSQL veritabanına veri taşıma
"""

from main import create_app
from models import db, User, UserRole, Department, DepartmentPermission
from datetime import datetime
import os

def migrate_to_postgres():
    """SQLite'dan PostgreSQL'e veri taşı"""
    try:
        print("🚀 PostgreSQL migration başlıyor...")
        
        app = create_app()
        
        with app.app_context():
            # Tabloları oluştur
            print("🗄️ PostgreSQL tabloları oluşturuluyor...")
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
            
            # Satış Departmanı oluştur
            sales_dept = Department.query.filter_by(name='Satış Departmanı').first()
            if not sales_dept:
                sales_dept = Department(
                    name='Satış Departmanı',
                    description='Satış ve pazarlama işlemleri'
                )
                db.session.add(sales_dept)
                print("🏢 Satış Departmanı oluşturuldu")
            
            # Teknik Dizel Departmanı oluştur
            tech_dept = Department.query.filter_by(name='Teknik Dizel').first()
            if not tech_dept:
                tech_dept = Department(
                    name='Teknik Dizel',
                    description='Admin departmanı'
                )
                db.session.add(tech_dept)
                print("🏢 Teknik Dizel departmanı oluşturuldu")
            
            db.session.commit()
            
            # Departman ID'lerini al
            if sales_dept.id:
                # Örnek departman yöneticisi oluştur
                manager = User.query.filter_by(username='manager1').first()
                if not manager:
                    manager = User(
                        username='manager1',
                        email='manager1@company.com',
                        first_name='Departman',
                        last_name='Yöneticisi',
                        role=UserRole.DEPARTMENT_MANAGER,
                        phone='0555 123 4567',
                        region='İstanbul',
                        department_id=sales_dept.id,
                        is_active=True
                    )
                    manager.set_password('manager123')
                    db.session.add(manager)
                    print("👤 Örnek departman yöneticisi oluşturuldu: manager1/manager123")
                
                # Örnek kullanıcı oluştur
                user = User.query.filter_by(username='user1').first()
                if not user:
                    user = User(
                        username='user1',
                        email='user1@company.com',
                        first_name='Mehmet',
                        last_name='Demir',
                        role=UserRole.USER,
                        department_id=sales_dept.id,
                        is_active=True
                    )
                    user.set_password('user123')
                    db.session.add(user)
                    print("👤 Örnek kullanıcı oluşturuldu: user1/user123")
                
                # Satış Departmanı için izinler oluştur
                permissions = [
                    {'module_name': 'sales', 'can_view': True, 'can_edit': True, 'can_delete': False},
                    {'module_name': 'returns', 'can_view': True, 'can_edit': True, 'can_delete': False},
                    {'module_name': 'tasks', 'can_view': True, 'can_edit': True, 'can_delete': False},
                    {'module_name': 'reports', 'can_view': True, 'can_edit': False, 'can_delete': False},
                    {'module_name': 'user_management', 'can_view': False, 'can_edit': False, 'can_delete': False}
                ]
                
                for perm_data in permissions:
                    existing_perm = DepartmentPermission.query.filter_by(
                        department_id=sales_dept.id,
                        module_name=perm_data['module_name']
                    ).first()
                    
                    if not existing_perm:
                        permission = DepartmentPermission(
                            department_id=sales_dept.id,
                            module_name=perm_data['module_name'],
                            can_view=perm_data['can_view'],
                            can_edit=perm_data['can_edit'],
                            can_delete=perm_data['can_delete']
                        )
                        db.session.add(permission)
                
                print("🔐 Satış Departmanı izinleri oluşturuldu")
            
            # Teknik Dizel için tam yetki
            if tech_dept.id:
                module_names = ['sales', 'tasks', 'returns', 'reports', 'user_management']
                for mod in module_names:
                    perm = DepartmentPermission.query.filter_by(department_id=tech_dept.id, module_name=mod).first()
                    if not perm:
                        perm = DepartmentPermission(
                            department_id=tech_dept.id,
                            module_name=mod,
                            can_view=True,
                            can_edit=True,
                            can_delete=True
                        )
                        db.session.add(perm)
                
                print("🔐 Teknik Dizel yetkileri oluşturuldu")
            
            db.session.commit()
            print("🎉 PostgreSQL migration başarıyla tamamlandı!")
            
    except Exception as e:
        print(f"❌ Migration hatası: {e}")
        db.session.rollback()
        raise e

if __name__ == '__main__':
    migrate_to_postgres()
