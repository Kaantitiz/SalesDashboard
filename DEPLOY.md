# 🚀 Sales Dashboard Deploy Talimatları

## Render.com'da Deploy

### 1. Repository'yi Render'a Bağla
- Render.com'da yeni bir Web Service oluştur
- GitHub repository'yi bağla
- Branch: `main` (veya ana branch)

### 2. Environment Variables Ayarla
Render Dashboard'da şu environment variables'ları ekle:

```bash
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-this-in-production
```

### 3. Build ve Start Commands
```bash
# Build Command
chmod +x build.sh && ./build.sh

# Start Command
gunicorn wsgi:app --bind 0.0.0.0:$PORT
```

### 4. PostgreSQL Database
- Render'da yeni PostgreSQL database oluştur
- Database name: `sales_dashboard`
- User: `sales_dashboard_user`
- Plan: Free

### 5. Auto-Deploy
- `autoDeploy: true` olarak ayarlandı
- Her push'ta otomatik deploy

## 🐛 Sorun Giderme

### Email NOT NULL Hatası
Eğer hala email constraint hatası alıyorsanız:

1. **PostgreSQL için:**
```sql
ALTER TABLE "user" ALTER COLUMN email DROP NOT NULL;
```

2. **SQLite için:**
```sql
-- Yeni tablo oluştur
CREATE TABLE user_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE,
    -- diğer alanlar...
);

-- Verileri kopyala
INSERT INTO user_new SELECT * FROM user;

-- Eski tabloyu sil ve yeniden adlandır
DROP TABLE user;
ALTER TABLE user_new RENAME TO user;
```

### Build Hatası
Eğer build hatası alıyorsanız:

1. Python sürümünü kontrol et (3.11.7)
2. Requirements.txt'deki paketleri kontrol et
3. Build log'larını incele

## 📊 Health Check
- Health check path: `/`
- Uygulama başarıyla çalışıyorsa 200 OK döner

## 🔒 Güvenlik
- Production'da SECRET_KEY değiştir
- HTTPS kullan (Render otomatik sağlar)
- Environment variables'ları güvenli tut

## 📝 Logs
Render Dashboard'da:
- Build logs
- Runtime logs
- Health check logs

## 🚀 Deploy Sonrası Test
1. Ana sayfa yükleniyor mu?
2. Login çalışıyor mu?
3. Kullanıcı silme işlemi çalışıyor mu?
4. API endpoint'leri çalışıyor mu?
