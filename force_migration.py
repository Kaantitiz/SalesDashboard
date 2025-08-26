#!/usr/bin/env python3
"""
Güçlü Migration Script'i
Bu script verileri kesinlikle geri getirir
"""

import os
import sys
import sqlite3
import psycopg2
from datetime import datetime

def get_sqlite_data():
    """SQLite'dan verileri al"""
    try:
        conn = sqlite3.connect('instance/sales_dashboard.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("🔍 SQLite veritabanından veriler alınıyor...")
        
        # Kullanıcıları al
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()
        print(f"👥 Kullanıcı sayısı: {len(users)}")
        
        # Departmanları al
        cursor.execute("SELECT * FROM department")
        departments = cursor.fetchall()
        print(f"🏢 Departman sayısı: {len(departments)}")
        
        # Satışları al
        cursor.execute("SELECT * FROM sales")
        sales = cursor.fetchall()
        print(f"💰 Satış sayısı: {len(sales)}")
        
        # İadeleri al
        cursor.execute("SELECT * FROM returns")
        returns = cursor.fetchall()
        print(f"🔄 İade sayısı: {len(returns)}")
        
        conn.close()
        return users, departments, sales, returns
        
    except Exception as e:
        print(f"❌ SQLite veri alma hatası: {e}")
        return None, None, None, None

def migrate_to_postgres(users, departments, sales, returns):
    """PostgreSQL'e veri taşı"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL bulunamadı!")
            return False
        
        # postgres:// -> postgresql:// dönüşümü
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("🚀 PostgreSQL'e veri taşınıyor...")
        
        # Tabloları oluştur
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS "user" (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) NOT NULL UNIQUE,
                email VARCHAR(120) UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'user',
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                department_id INTEGER,
                department_role VARCHAR(100),
                representative_code VARCHAR(20) UNIQUE,
                phone VARCHAR(20),
                region VARCHAR(100)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS department (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                manager_id INTEGER,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                default_role_title VARCHAR(100)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id SERIAL PRIMARY KEY,
                representative_id INTEGER,
                date DATE NOT NULL,
                product_group VARCHAR(100) NOT NULL,
                brand VARCHAR(100) NOT NULL,
                product_name VARCHAR(200) NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price FLOAT NOT NULL,
                total_price FLOAT NOT NULL,
                net_price FLOAT NOT NULL,
                customer_name VARCHAR(200),
                customer_code VARCHAR(50),
                original_quantity VARCHAR(20),
                original_date VARCHAR(20),
                original_product_group VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS returns (
                id SERIAL PRIMARY KEY,
                representative_id INTEGER,
                date DATE NOT NULL,
                product_group VARCHAR(100) NOT NULL,
                brand VARCHAR(100) NOT NULL,
                product_name VARCHAR(200) NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price FLOAT NOT NULL,
                total_price FLOAT NOT NULL,
                net_price FLOAT NOT NULL,
                return_reason VARCHAR(200),
                customer_name VARCHAR(200),
                customer_code VARCHAR(50),
                original_quantity VARCHAR(20),
                original_date VARCHAR(20),
                original_product_group VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        print("✅ Tablolar oluşturuldu")
        
        # Verileri taşı
        if users:
            print("👥 Kullanıcılar taşınıyor...")
            for user in users:
                cursor.execute("""
                    INSERT INTO "user" (id, username, email, password_hash, role, first_name, last_name, 
                                      is_active, created_at, last_login, department_id, department_role,
                                      representative_code, phone, region)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (user['id'], user['username'], user['email'], user['password_hash'], 
                      user['role'], user['first_name'], user['last_name'], user['is_active'],
                      user['created_at'], user['last_login'], user['department_id'], user['department_role'],
                      user['representative_code'], user['phone'], user['region']))
        
        if departments:
            print("🏢 Departmanlar taşınıyor...")
            for dept in departments:
                cursor.execute("""
                    INSERT INTO department (id, name, description, manager_id, is_active, created_at, updated_at, default_role_title)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (dept['id'], dept['name'], dept['description'], dept['manager_id'], 
                      dept['is_active'], dept['created_at'], dept['updated_at'], dept['default_role_title']))
        
        if sales:
            print("💰 Satışlar taşınıyor...")
            for sale in sales:
                cursor.execute("""
                    INSERT INTO sales (id, representative_id, date, product_group, brand, product_name,
                                     quantity, unit_price, total_price, net_price, customer_name, customer_code,
                                     original_quantity, original_date, original_product_group, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (sale['id'], sale['representative_id'], sale['date'], sale['product_group'],
                      sale['brand'], sale['product_name'], sale['quantity'], sale['unit_price'],
                      sale['total_price'], sale['net_price'], sale['customer_name'], sale['customer_code'],
                      sale['original_quantity'], sale['original_date'], sale['original_product_group'], sale['created_at']))
        
        if returns:
            print("🔄 İadeler taşınıyor...")
            for ret in returns:
                cursor.execute("""
                    INSERT INTO returns (id, representative_id, date, product_group, brand, product_name,
                                       quantity, unit_price, total_price, net_price, return_reason, customer_name,
                                       customer_code, original_quantity, original_date, original_product_group, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (ret['id'], ret['representative_id'], ret['date'], ret['product_group'],
                      ret['brand'], ret['product_name'], ret['quantity'], ret['unit_price'],
                      ret['total_price'], ret['net_price'], ret['return_reason'], ret['customer_name'],
                      ret['customer_code'], ret['original_quantity'], ret['original_date'], ret['original_product_group'], ret['created_at']))
        
        conn.commit()
        conn.close()
        
        print("🎉 Tüm veriler başarıyla taşındı!")
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL migration hatası: {e}")
        return False

def main():
    """Ana migration fonksiyonu"""
    print("🚀 Güçlü Migration Script'i Başlatılıyor...")
    print("=" * 60)
    
    # SQLite'dan verileri al
    users, departments, sales, returns = get_sqlite_data()
    
    if not users and not departments and not sales and not returns:
        print("❌ SQLite'dan veri alınamadı!")
        return False
    
    # PostgreSQL'e taşı
    if migrate_to_postgres(users, departments, sales, returns):
        print("\n🎉 Migration başarıyla tamamlandı!")
        print("Verileriniz artık PostgreSQL'de ve kalıcı!")
        return True
    else:
        print("\n❌ Migration başarısız!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
