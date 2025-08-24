#!/usr/bin/env python3
"""
Direkt SQLite ile veritabanı oluşturma
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

def create_direct_db():
    """Direkt SQLite ile veritabanı oluştur"""
    try:
        print("🚀 Direkt veritabanı oluşturuluyor...")
        
        # Veritabanı dosyasını sil (eğer varsa)
        db_file = 'sales_dashboard.db'
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"🗑️ Eski veritabanı silindi: {db_file}")
        
        # Yeni veritabanı oluştur
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        print("🗄️ Tablolar oluşturuluyor...")
        
        # User tablosu
        cursor.execute('''
            CREATE TABLE user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                first_name VARCHAR(80),
                last_name VARCHAR(80),
                role VARCHAR(20),
                phone VARCHAR(20),
                region VARCHAR(100),
                department_id INTEGER,
                is_active BOOLEAN DEFAULT TRUE,
                password_hash VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Department tablosu
        cursor.execute('''
            CREATE TABLE department (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Sales tablosu
        cursor.execute('''
            CREATE TABLE sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_no VARCHAR(50),
                customer_name VARCHAR(100),
                product_name VARCHAR(200),
                quantity INTEGER,
                unit_price DECIMAL(10,2),
                total_amount DECIMAL(10,2),
                sale_date DATE,
                user_id INTEGER,
                department_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        print("✅ Tablolar oluşturuldu")
        
        # Departman oluştur
        cursor.execute('''
            INSERT INTO department (name, description) 
            VALUES (?, ?)
        ''', ('Genel', 'Genel departman'))
        
        dept_id = cursor.lastrowid
        print(f"🏢 Departman oluşturuldu: ID {dept_id}")
        
        # Admin kullanıcısı oluştur
        password_hash = generate_password_hash('admin123')
        cursor.execute('''
            INSERT INTO user (username, email, first_name, last_name, role, is_active, password_hash, department_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('admin', 'admin@company.com', 'Admin', 'User', 'ADMIN', 1, password_hash, dept_id))
        
        print("👤 Admin kullanıcısı oluşturuldu: admin/admin123")
        
        # Test kullanıcıları
        test_users = [
            ('manager1', 'manager1@company.com', 'Manager', 'User', 'MANAGER', 1, generate_password_hash('manager123'), dept_id),
            ('user1', 'user1@company.com', 'Normal', 'User', 'USER', 1, generate_password_hash('user123'), dept_id)
        ]
        
        for user_data in test_users:
            cursor.execute('''
                INSERT INTO user (username, email, first_name, last_name, role, is_active, password_hash, department_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', user_data)
        
        print("👥 Test kullanıcıları oluşturuldu")
        
        conn.commit()
        conn.close()
        
        print("🎉 Veritabanı başarıyla oluşturuldu!")
        print("📋 Kullanıcı bilgileri:")
        print("   - admin/admin123 (ADMIN)")
        print("   - manager1/manager123 (MANAGER)")
        print("   - user1/user123 (USER)")
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    create_direct_db()
