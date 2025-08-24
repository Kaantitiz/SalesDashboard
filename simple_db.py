#!/usr/bin/env python3
"""
Çok basit veritabanı oluşturma
"""

import sqlite3
import os

def create_simple_db():
    """Basit veritabanı oluştur"""
    try:
        print("🚀 Basit veritabanı oluşturuluyor...")
        
        # Veritabanı dosyası
        db_file = 'sales_dashboard.db'
        
        # Eski dosyayı sil
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"🗑️ Eski veritabanı silindi")
        
        # Yeni veritabanı
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        print("🗄️ Tablolar oluşturuluyor...")
        
        # User tablosu - çok basit
        cursor.execute('''
            CREATE TABLE user (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password_hash TEXT,
                email TEXT,
                role TEXT
            )
        ''')
        
        # Department tablosu
        cursor.execute('''
            CREATE TABLE department (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        ''')
        
        print("✅ Tablolar oluşturuldu")
        
        # Departman ekle
        cursor.execute('INSERT INTO department (id, name) VALUES (?, ?)', (1, 'Genel'))
        
        # Admin kullanıcısı - basit hash
        import hashlib
        password = 'admin123'
        password_hash = hashlib.md5(password.encode()).hexdigest()
        
        cursor.execute('''
            INSERT INTO user (username, password_hash, email, role) 
            VALUES (?, ?, ?, ?)
        ''', ('admin', password_hash, 'admin@company.com', 'ADMIN'))
        
        print("👤 Admin kullanıcısı oluşturuldu: admin/admin123")
        
        conn.commit()
        conn.close()
        
        print("🎉 Veritabanı hazır!")
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    create_simple_db()
