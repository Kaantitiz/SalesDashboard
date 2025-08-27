import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # Veritabanı URL'i - PostgreSQL öncelikli
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if DATABASE_URL:
        # PostgreSQL URL'i varsa kullan
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        
        try:
            # Test connection
            import psycopg2
            SQLALCHEMY_DATABASE_URI = DATABASE_URL
            print("✅ PostgreSQL bağlantısı kuruldu")
        except ImportError:
            print("⚠️ PostgreSQL paketi bulunamadı, psycopg2-binary yükleniyor...")
            import subprocess
            import sys
            subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
            import psycopg2
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
            SQLALCHEMY_DATABASE_URI = DATABASE_URL
            print("✅ PostgreSQL bağlantısı kuruldu")
    else:
        # Geliştirme ortamında SQLite kullan
        if os.environ.get('FLASK_ENV') == 'development':
            SQLALCHEMY_DATABASE_URI = 'sqlite:///sales_dashboard.db'
            print("🔧 Geliştirme ortamında SQLite kullanılıyor")
        else:
            # Production ortamında PostgreSQL gerekli
            SQLALCHEMY_DATABASE_URI = 'sqlite:///sales_dashboard.db'  # Geçici olarak SQLite
            print("⚠️ Production ortamında DATABASE_URL bulunamadı, SQLite kullanılıyor")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT ayarları
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # API ayarları
    API_BASE_URL = os.environ.get('API_BASE_URL') or 'http://localhost:5000/api'
    
    # Hedef değerleri
    TARGET_VALUE = 100000000  # 100 milyon TL
    MONTHLY_TARGET = 10000000  # 10 milyon TL aylık
    
    # Dosya yükleme ayarları - Kalıcı depolama için
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/opt/render/project/src/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Renk paleti
    COLORS = {
        'primary': '#2d6cdf',
        'secondary': '#6c757d',
        'danger': '#e74c3c',
        'warning': '#f1c40f',
        'info': '#17a2b8',
        'dark': '#222f3e',
        'light': '#f8f9fa',
        'success': '#27ae60'
    } 

    # Uyumsoft API Ayarları
    UYUMSOFT_API_URL = "https://api.uyumsoft.com"  # Uyumsoft API URL'inizi buraya yazın
    UYUMSOFT_USERNAME = "your_username"  # Uyumsoft kullanıcı adınız
    UYUMSOFT_PASSWORD = "your_password"  # Uyumsoft şifreniz
    UYUMSOFT_COMPANY_ID = "your_company_id"  # Şirket ID'niz (gerekirse)
    
    # Uyumsoft API Timeout Ayarları
    UYUMSOFT_TIMEOUT = 30  # saniye
    UYUMSOFT_MAX_RETRIES = 3 