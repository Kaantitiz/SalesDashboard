#!/usr/bin/env python3
"""
Çok basit admin kullanıcısı oluşturma
"""

import os
import sys

# Flask app context'i olmadan çalışacak
def create_simple_user():
    try:
        # SQLite veritabanı dosyasını kontrol et
        db_path = 'sales_dashboard.db'
        
        if os.path.exists(db_path):
            print(f"✅ Veritabanı dosyası mevcut: {db_path}")
        else:
            print(f"❌ Veritabanı dosyası bulunamadı: {db_path}")
            return
        
        # SQLite ile direkt bağlan
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Tabloları kontrol et
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📋 Mevcut tablolar: {[t[0] for t in tables]}")
        
        # User tablosunu kontrol et
        if ('user',) in tables:
            print("✅ User tablosu mevcut")
            
            # Admin kullanıcısını kontrol et
            cursor.execute("SELECT username FROM user WHERE username='admin';")
            existing = cursor.fetchone()
            
            if existing:
                print("👤 Admin kullanıcısı zaten mevcut")
            else:
                # Admin kullanıcısı oluştur
                from werkzeug.security import generate_password_hash
                password_hash = generate_password_hash('admin123')
                
                cursor.execute("""
                    INSERT INTO user (username, email, first_name, last_name, role, is_active, password_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ('admin', 'admin@company.com', 'Admin', 'User', 'ADMIN', 1, password_hash))
                
                conn.commit()
                print("👤 Admin kullanıcısı oluşturuldu: admin/admin123")
        else:
            print("❌ User tablosu bulunamadı")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    create_simple_user()
