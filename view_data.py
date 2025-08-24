#!/usr/bin/env python3
"""
SQLite veritabanındaki verileri görüntüleme
"""

import sqlite3
import os

def view_database_data():
    """Veritabanındaki tüm verileri görüntüle"""
    try:
        print("🔍 SQLite veritabanı verileri görüntüleniyor...")
        
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
        
        print(f"\n📋 Mevcut tablolar: {[t[0] for t in tables]}")
        
        # Her tablodaki verileri göster
        for table in tables:
            table_name = table[0]
            print(f"\n{'='*50}")
            print(f"📊 TABLO: {table_name}")
            print(f"{'='*50}")
            
            try:
                # Tablo yapısını göster
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                print("📋 Sütunlar:")
                for col in columns:
                    print(f"   - {col[1]} ({col[2]})")
                
                # Veri sayısını göster
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                print(f"📊 Toplam kayıt: {count}")
                
                # İlk 10 kaydı göster
                if count > 0:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 10;")
                    rows = cursor.fetchall()
                    print("📝 İlk 10 kayıt:")
                    for i, row in enumerate(rows, 1):
                        print(f"   {i}. {row}")
                else:
                    print("📝 Veri yok")
                    
            except Exception as e:
                print(f"❌ Tablo okuma hatası: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    view_database_data()
