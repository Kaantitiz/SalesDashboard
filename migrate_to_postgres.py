#!/usr/bin/env python3
"""
SQLite'dan PostgreSQL'e veri taşıma scripti
Bu script mevcut SQLite veritabanındaki verileri PostgreSQL'e taşır
"""

import os
import sys
import sqlite3
from datetime import datetime
from main import create_app
from models import db, User, UserRole, Department, DepartmentPermission, Sales, Returns, Planning, Target, ActivityLog

def migrate_sqlite_to_postgres():
    """SQLite'dan PostgreSQL'e veri taşı"""
    try:
        print("🚀 SQLite'dan PostgreSQL'e veri taşıma başlıyor...")
        
        # SQLite veritabanı dosyası
        sqlite_db_path = 'instance/sales_dashboard.db'
        
        if not os.path.exists(sqlite_db_path):
            print(f"❌ SQLite veritabanı bulunamadı: {sqlite_db_path}")
            return
        
        # SQLite bağlantısı
        sqlite_conn = sqlite3.connect(sqlite_db_path)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Flask app'i başlat
        app = create_app()
        
        with app.app_context():
            # PostgreSQL tablolarını oluştur
            print("🗄️ PostgreSQL tabloları oluşturuluyor...")
            db.create_all()
            print("✅ Tablolar oluşturuldu")
            
            # Kullanıcıları taşı
            print("👥 Kullanıcılar taşınıyor...")
            sqlite_cursor.execute("SELECT * FROM user")
            users = sqlite_cursor.fetchall()
            
            for user_data in users:
                # SQLite'dan gelen veriyi kontrol et
                if len(user_data) >= 8:  # En az gerekli alan sayısı
                    user = User(
                        id=user_data[0],
                        username=user_data[1],
                        email=user_data[2],
                        password_hash=user_data[3],
                        role=UserRole(user_data[4]) if user_data[4] else UserRole.USER,
                        first_name=user_data[5] or '',
                        last_name=user_data[6] or '',
                        is_active=bool(user_data[7]) if user_data[7] is not None else True,
                        created_at=datetime.fromisoformat(user_data[8]) if len(user_data) > 8 and user_data[8] else datetime.utcnow(),
                        last_login=datetime.fromisoformat(user_data[9]) if len(user_data) > 9 and user_data[9] else None,
                        department_id=user_data[10] if len(user_data) > 10 else None,
                        department_role=user_data[11] if len(user_data) > 11 else None,
                        representative_code=user_data[12] if len(user_data) > 12 else None,
                        phone=user_data[13] if len(user_data) > 13 else None,
                        region=user_data[14] if len(user_data) > 14 else None
                    )
                    
                    # ID'yi manuel olarak ayarla
                    db.session.add(user)
                    db.session.flush()  # ID'yi almak için flush
                    
                    # ID'yi orijinal değere geri ayarla
                    user.id = user_data[0]
                    db.session.flush()
            
            print(f"✅ {len(users)} kullanıcı taşındı")
            
            # Departmanları taşı
            print("🏢 Departmanlar taşınıyor...")
            sqlite_cursor.execute("SELECT * FROM department")
            departments = sqlite_cursor.fetchall()
            
            for dept_data in departments:
                if len(dept_data) >= 4:
                    dept = Department(
                        id=dept_data[0],
                        name=dept_data[1],
                        description=dept_data[2],
                        manager_id=dept_data[3],
                        is_active=bool(dept_data[4]) if len(dept_data) > 4 else True,
                        created_at=datetime.fromisoformat(dept_data[5]) if len(dept_data) > 5 and dept_data[5] else datetime.utcnow(),
                        updated_at=datetime.fromisoformat(dept_data[6]) if len(dept_data) > 6 and dept_data[6] else datetime.utcnow(),
                        default_role_title=dept_data[7] if len(dept_data) > 7 else None
                    )
                    
                    db.session.add(dept)
                    db.session.flush()
                    dept.id = dept_data[0]
                    db.session.flush()
            
            print(f"✅ {len(departments)} departman taşındı")
            
            # Satış verilerini taşı
            print("💰 Satış verileri taşınıyor...")
            try:
                sqlite_cursor.execute("SELECT * FROM sales")
                sales_data = sqlite_cursor.fetchall()
                
                for sale_data in sales_data:
                    if len(sale_data) >= 8:
                        sale = Sales(
                            id=sale_data[0],
                            representative_id=sale_data[1],
                            customer_name=sale_data[2],
                            product_name=sale_data[3],
                            quantity=sale_data[4],
                            unit_price=sale_data[5],
                            total_amount=sale_data[6],
                            sale_date=datetime.fromisoformat(sale_data[7]) if sale_data[7] else datetime.utcnow(),
                            notes=sale_data[8] if len(sale_data) > 8 else None,
                            created_at=datetime.fromisoformat(sale_data[9]) if len(sale_data) > 9 and sale_data[9] else datetime.utcnow()
                        )
                        
                        db.session.add(sale)
                        db.session.flush()
                        sale.id = sale_data[0]
                        db.session.flush()
                
                print(f"✅ {len(sales_data)} satış kaydı taşındı")
            except Exception as e:
                print(f"⚠️ Satış verileri taşınırken hata: {e}")
            
            # Planlama verilerini taşı
            print("📅 Planlama verileri taşınıyor...")
            try:
                sqlite_cursor.execute("SELECT * FROM planning")
                planning_data = sqlite_cursor.fetchall()
                
                for plan_data in planning_data:
                    if len(plan_data) >= 7:
                        plan = Planning(
                            id=plan_data[0],
                            representative_id=plan_data[1],
                            title=plan_data[2],
                            description=plan_data[3],
                            start_date=datetime.fromisoformat(plan_data[4]) if plan_data[4] else datetime.utcnow(),
                            end_date=datetime.fromisoformat(plan_data[5]) if plan_data[5] else datetime.utcnow(),
                            status=plan_data[6],
                            priority=plan_data[7] if len(plan_data) > 7 else 'medium',
                            created_at=datetime.fromisoformat(plan_data[8]) if len(plan_data) > 8 and plan_data[8] else datetime.utcnow()
                        )
                        
                        db.session.add(plan)
                        db.session.flush()
                        plan.id = plan_data[0]
                        db.session.flush()
                
                print(f"✅ {len(planning_data)} planlama kaydı taşındı")
            except Exception as e:
                print(f"⚠️ Planlama verileri taşınırken hata: {e}")
            
            # Hedef verilerini taşı
            print("🎯 Hedef verileri taşınıyor...")
            try:
                sqlite_cursor.execute("SELECT * FROM target")
                target_data = sqlite_cursor.fetchall()
                
                for target_row in target_data:
                    if len(target_row) >= 5:
                        target = Target(
                            id=target_row[0],
                            user_id=target_row[1],
                            target_amount=target_row[2],
                            target_month=target_row[3],
                            target_year=target_row[4],
                            created_at=datetime.fromisoformat(target_row[5]) if len(target_row) > 5 and target_row[5] else datetime.utcnow()
                        )
                        
                        db.session.add(target)
                        db.session.flush()
                        target.id = target_row[0]
                        db.session.flush()
                
                print(f"✅ {len(target_data)} hedef kaydı taşındı")
            except Exception as e:
                print(f"⚠️ Hedef verileri taşınırken hata: {e}")
            
            # İade verilerini taşı
            print("↩️ İade verileri taşınıyor...")
            try:
                sqlite_cursor.execute("SELECT * FROM returns")
                returns_data = sqlite_cursor.fetchall()
                
                for return_data in returns_data:
                    if len(return_data) >= 8:
                        return_record = Returns(
                            id=return_data[0],
                            representative_id=return_data[1],
                            customer_name=return_data[2],
                            product_name=return_data[3],
                            quantity=return_data[4],
                            return_reason=return_data[5],
                            return_date=datetime.fromisoformat(return_data[6]) if return_data[6] else datetime.utcnow(),
                            amount=return_data[7],
                            notes=return_data[8] if len(return_data) > 8 else None,
                            created_at=datetime.fromisoformat(return_data[9]) if len(return_data) > 9 and return_data[9] else datetime.utcnow()
                        )
                        
                        db.session.add(return_record)
                        db.session.flush()
                        return_record.id = return_data[0]
                        db.session.flush()
                
                print(f"✅ {len(returns_data)} iade kaydı taşındı")
            except Exception as e:
                print(f"⚠️ İade verileri taşınırken hata: {e}")
            
            # Tüm değişiklikleri kaydet
            db.session.commit()
            print("💾 Tüm veriler PostgreSQL'e kaydedildi")
            
            # SQLite bağlantısını kapat
            sqlite_conn.close()
            
            print("🎉 Migration başarıyla tamamlandı!")
            print("📊 Artık verileriniz Render'da kalıcı olarak saklanacak!")
            
    except Exception as e:
        print(f"❌ Migration hatası: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        if 'sqlite_conn' in locals():
            sqlite_conn.close()

if __name__ == '__main__':
    migrate_sqlite_to_postgres()
