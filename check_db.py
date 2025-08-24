#!/usr/bin/env python3
"""
Veritabanı durumunu kontrol etme
"""

import sqlite3
import os

def check_database():
    """Veritabanı durumunu kontrol et"""
    try:
        print("🔍 Veritabanı durumu kontrol ediliyor...")
        
        db_file = 'sales_dashboard.db'
        
        # Dosya var mı?
        if os.path.exists(db_file):
            print(f"✅ Veritabanı dosyası mevcut: {db_file}")
            print(f"📏 Dosya boyutu: {os.path.getsize(db_file)} bytes")
        else:
            print(f"❌ Veritabanı dosyası bulunamadı: {db_file}")
            return
        
        # Veritabanına bağlan
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Tabloları listele
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"📋 Mevcut tablolar: {[t[0] for t in tables]}")
        
        # User tablosunu kontrol et
        if ('user',) in tables:
            print("✅ User tablosu mevcut")
            
            # Kullanıcıları listele
            cursor.execute("SELECT username, email, role FROM user;")
            users = cursor.fetchall()
            
            if users:
                print(f"👥 Kullanıcı sayısı: {len(users)}")
                for user in users:
                    print(f"   - {user[0]} ({user[1]}) - {user[2]}")
            else:
                print("❌ Hiç kullanıcı yok!")
        else:
            print("❌ User tablosu bulunamadı!")
        
        # Department tablosunu kontrol et
        if ('department',) in tables:
            print("✅ Department tablosu mevcut")
            
            cursor.execute("SELECT id, name FROM department;")
            depts = cursor.fetchall()
            
            if depts:
                print(f"🏢 Departman sayısı: {len(depts)}")
                for dept in depts:
                    print(f"   - ID {dept[0]}: {dept[1]}")
            else:
                print("❌ Hiç departman yok!")
        else:
            print("❌ Department tablosu bulunamadı!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_database()
