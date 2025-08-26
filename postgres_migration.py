#!/usr/bin/env python3
"""
PostgreSQL Migration Script
Bu script mevcut SQLite veritabanındaki verileri PostgreSQL'e taşır
"""

import os
import sys
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json

def get_sqlite_connection():
    """SQLite veritabanına bağlanır"""
    try:
        conn = sqlite3.connect('instance/sales_dashboard.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"❌ SQLite bağlantı hatası: {e}")
        return None

def get_postgres_connection():
    """PostgreSQL veritabanına bağlanır"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL environment variable bulunamadı!")
            return None
        
        # postgres:// -> postgresql:// dönüşümü
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        print(f"❌ PostgreSQL bağlantı hatası: {e}")
        return None

def create_postgres_tables(conn):
    """PostgreSQL'de tabloları oluşturur"""
    try:
        cursor = conn.cursor()
        
        # Departments tablosu
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
        
        # Users tablosu
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
                department_id INTEGER REFERENCES department(id),
                department_role VARCHAR(100),
                representative_code VARCHAR(20) UNIQUE,
                phone VARCHAR(20),
                region VARCHAR(100)
            )
        """)
        
        # Sales tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id SERIAL PRIMARY KEY,
                representative_id INTEGER REFERENCES "user"(id),
                customer_name VARCHAR(255) NOT NULL,
                product_name VARCHAR(255) NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                total_amount DECIMAL(10,2) NOT NULL,
                sale_date DATE NOT NULL,
                region VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Returns tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS returns (
                id SERIAL PRIMARY KEY,
                representative_id INTEGER REFERENCES "user"(id),
                customer_name VARCHAR(255) NOT NULL,
                product_name VARCHAR(255) NOT NULL,
                quantity INTEGER NOT NULL,
                return_reason TEXT,
                return_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Planning tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS planning (
                id SERIAL PRIMARY KEY,
                representative_id INTEGER REFERENCES "user"(id),
                plan_date DATE NOT NULL,
                target_amount DECIMAL(10,2) NOT NULL,
                notes TEXT,
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Targets tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS target (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES "user"(id),
                target_amount DECIMAL(10,2) NOT NULL,
                target_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Activity Logs tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES "user"(id),
                action VARCHAR(100) NOT NULL,
                details TEXT,
                ip_address VARCHAR(45),
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        print("✅ PostgreSQL tabloları oluşturuldu")
        return True
        
    except Exception as e:
        print(f"❌ Tablo oluşturma hatası: {e}")
        conn.rollback()
        return False

def migrate_data(sqlite_conn, postgres_conn):
    """Verileri SQLite'dan PostgreSQL'e taşır"""
    try:
        sqlite_cursor = sqlite_conn.cursor()
        postgres_cursor = postgres_conn.cursor()
        
        # Departments
        print("🔄 Departments taşınıyor...")
        sqlite_cursor.execute("SELECT * FROM department")
        departments = sqlite_cursor.fetchall()
        
        for dept in departments:
            postgres_cursor.execute("""
                INSERT INTO department (id, name, description, manager_id, is_active, created_at, updated_at, default_role_title)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (dept['id'], dept['name'], dept['description'], dept['manager_id'], 
                  dept['is_active'], dept['created_at'], dept['updated_at'], dept['default_role_title']))
        
        # Users
        print("🔄 Users taşınıyor...")
        sqlite_cursor.execute("SELECT * FROM user")
        users = sqlite_cursor.fetchall()
        
        for user in users:
            postgres_cursor.execute("""
                INSERT INTO "user" (id, username, email, password_hash, role, first_name, last_name, 
                                  is_active, created_at, last_login, department_id, department_role,
                                  representative_code, phone, region)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (user['id'], user['username'], user['email'], user['password_hash'], 
                  user['role'], user['first_name'], user['last_name'], user['is_active'],
                  user['created_at'], user['last_login'], user['department_id'], user['department_role'],
                  user['representative_code'], user['phone'], user['region']))
        
        # Sales
        print("🔄 Sales taşınıyor...")
        sqlite_cursor.execute("SELECT * FROM sales")
        sales = sqlite_cursor.fetchall()
        
        for sale in sales:
            postgres_cursor.execute("""
                INSERT INTO sales (id, representative_id, customer_name, product_name, quantity, 
                                 unit_price, total_amount, sale_date, region, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (sale['id'], sale['representative_id'], sale['customer_name'], sale['product_name'],
                  sale['quantity'], sale['unit_price'], sale['total_amount'], sale['sale_date'],
                  sale['region'], sale['created_at']))
        
        # Returns
        print("🔄 Returns taşınıyor...")
        sqlite_cursor.execute("SELECT * FROM returns")
        returns = sqlite_cursor.fetchall()
        
        for ret in returns:
            postgres_cursor.execute("""
                INSERT INTO returns (id, representative_id, customer_name, product_name, quantity,
                                   return_reason, return_date, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (ret['id'], ret['representative_id'], ret['customer_name'], ret['product_name'],
                  ret['quantity'], ret['return_reason'], ret['return_date'], ret['created_at']))
        
        # Planning
        print("🔄 Planning taşınıyor...")
        sqlite_cursor.execute("SELECT * FROM planning")
        planning = sqlite_cursor.fetchall()
        
        for plan in planning:
            postgres_cursor.execute("""
                INSERT INTO planning (id, representative_id, plan_date, target_amount, notes, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (plan['id'], plan['representative_id'], plan['plan_date'], plan['target_amount'],
                  plan['notes'], plan['status'], plan['created_at']))
        
        # Targets
        print("🔄 Targets taşınıyor...")
        sqlite_cursor.execute("SELECT * FROM target")
        targets = sqlite_cursor.fetchall()
        
        for target in targets:
            postgres_cursor.execute("""
                INSERT INTO target (id, user_id, target_amount, target_date, created_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (target['id'], target['user_id'], target['target_amount'], 
                  target['target_date'], target['created_at']))
        
        # Activity Logs
        print("🔄 Activity Logs taşınıyor...")
        sqlite_cursor.execute("SELECT * FROM activity_log")
        logs = sqlite_cursor.fetchall()
        
        for log in logs:
            postgres_cursor.execute("""
                INSERT INTO activity_log (id, user_id, action, details, ip_address, user_agent, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (log['id'], log['user_id'], log['action'], log['details'],
                  log['ip_address'], log['user_agent'], log['created_at']))
        
        postgres_conn.commit()
        print("✅ Tüm veriler başarıyla taşındı!")
        return True
        
    except Exception as e:
        print(f"❌ Veri taşıma hatası: {e}")
        postgres_conn.rollback()
        return False

def main():
    """Ana migration fonksiyonu"""
    print("🚀 PostgreSQL Migration başlatılıyor...")
    
    # SQLite bağlantısı
    sqlite_conn = get_sqlite_connection()
    if not sqlite_conn:
        print("❌ SQLite bağlantısı kurulamadı!")
        return False
    
    # PostgreSQL bağlantısı
    postgres_conn = get_postgres_connection()
    if not postgres_conn:
        print("❌ PostgreSQL bağlantısı kurulamadı!")
        sqlite_conn.close()
        return False
    
    try:
        # Tabloları oluştur
        if not create_postgres_tables(postgres_conn):
            return False
        
        # Verileri taşı
        if not migrate_data(sqlite_conn, postgres_conn):
            return False
        
        print("🎉 Migration başarıyla tamamlandı!")
        return True
        
    finally:
        sqlite_conn.close()
        postgres_conn.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
