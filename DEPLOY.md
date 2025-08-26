# 🚀 Sales Dashboard Deployment Guide

## 📋 Ön Gereksinimler

- Render hesabı
- Python 3.11+ bilgisi
- Git repository

## 🔧 Kalıcılık Sorunları ve Çözümleri

### ❌ Mevcut Sorunlar:
1. **Veritabanı Sıfırlanması**: Uyku modunda SQLite verileri kayboluyor
2. **Dosya Kaybı**: Upload edilen dosyalar kalıcı olmuyor
3. **Session Kaybı**: Kullanıcı oturumları korunmuyor

### ✅ Çözümler:
1. **PostgreSQL Veritabanı**: Kalıcı cloud veritabanı
2. **Kalıcı Depolama**: Render disk storage
3. **Environment Variables**: Güvenli konfigürasyon

## 🚀 Deployment Adımları

### 1. Render Dashboard'a Git
- [render.com](https://render.com) hesabınıza giriş yapın
- "New +" > "Web Service" seçin

### 2. Repository Bağlantısı
- GitHub/GitLab repository'nizi bağlayın
- Branch: `main` veya `master`

### 3. Service Konfigürasyonu
```
Name: salesdashboard
Environment: Python
Region: Frankfurt (EU) veya en yakın
Branch: main
Root Directory: ./
Build Command: chmod +x build.sh && ./build.sh
Start Command: gunicorn wsgi:app --bind 0.0.0.0:$PORT
```

### 4. Environment Variables
```
PYTHON_VERSION=3.11.7
FLASK_ENV=production
FLASK_APP=app.py
PYTHONPATH=.
```

### 5. Database Bağlantısı
- "New +" > "PostgreSQL" seçin
- Plan: Free
- Database Name: sales_dashboard
- User: sales_dashboard_user

### 6. Disk Storage (ÖNEMLİ!)
- Service > Settings > Disk
- Add Disk:
  - Name: persistent-storage
  - Mount Path: /opt/render/project/src/uploads
  - Size: 1 GB

## 🔄 Migration Sonrası

### Veri Taşıma:
```bash
# Local'de çalıştır
python postgres_migration.py
```

### Veritabanı Kontrol:
```bash
# Render console'da
python check_db.py
```

## 📁 Dosya Yapısı

```
WTC 25.08/
├── app.py                 # Ana uygulama
├── models.py             # Veritabanı modelleri
├── postgres_migration.py # Migration script
├── render.yaml           # Render konfigürasyonu
├── build.sh             # Build script
├── requirements.txt      # Python dependencies
└── uploads/             # Kalıcı dosya depolama
```

## 🚨 Önemli Notlar

### 1. **Veritabanı Kalıcılığı**
- SQLite yerine PostgreSQL kullanın
- DATABASE_URL environment variable'ı zorunlu
- Migration script'i otomatik çalışır

### 2. **Dosya Kalıcılığı**
- Uploads klasörü kalıcı disk'e mount edilir
- Dosya yolları otomatik güncellenir
- 1GB depolama alanı ayrılır

### 3. **Environment Variables**
- SECRET_KEY otomatik generate edilir
- JWT_SECRET_KEY otomatik generate edilir
- Production modunda SQLite kullanılamaz

## 🔍 Troubleshooting

### Migration Hatası:
```bash
# Render console'da
python postgres_migration.py
```

### Veritabanı Bağlantı Hatası:
```bash
# Environment variables kontrol
echo $DATABASE_URL
```

### Disk Mount Hatası:
- Settings > Disk bölümünü kontrol edin
- Mount path: `/opt/render/project/src/uploads`

## 📊 Monitoring

### Health Check:
- Endpoint: `/`
- Status: 200 OK
- Response Time: < 2s

### Logs:
- Render Dashboard > Logs
- Real-time log takibi
- Error monitoring

## 🔒 Güvenlik

### Environment Variables:
- SECRET_KEY: Otomatik generate
- DATABASE_URL: Render PostgreSQL
- FLASK_ENV: production

### Database:
- PostgreSQL SSL bağlantı
- User isolation
- Connection pooling

## 📈 Performance

### Database:
- PostgreSQL connection pooling
- Index optimization
- Query caching

### File Storage:
- SSD disk storage
- CDN integration (opsiyonel)
- File compression

## 🎯 Sonraki Adımlar

1. **Monitoring**: Log aggregation
2. **Backup**: Otomatik veritabanı yedekleme
3. **Scaling**: Plan upgrade (gerekirse)
4. **CDN**: Statik dosya optimizasyonu

---

## 📞 Destek

Sorun yaşarsanız:
1. Render Logs kontrol edin
2. Migration script'i çalıştırın
3. Environment variables kontrol edin
4. Disk storage mount kontrol edin

**Not**: Bu guide ile uygulamanız uyku modunda veri kaybetmeyecek ve kalıcı olacaktır! 🎉
