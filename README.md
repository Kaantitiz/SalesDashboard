# Sales Dashboard - Flask Uygulaması

Bu proje, satış departmanı için geliştirilmiş bir raporlama ve yönetim uygulamasıdır.

## 🚀 Hızlı Başlangıç

### Local Development
```bash
# Gereksinimleri yükle
pip install -r requirements.txt

# Veritabanını başlat
python main.py

# Tarayıcıda aç: http://localhost:5000
```

### Production Deployment (Render)

1. **GitHub'a yükle:**
```bash
git add .
git commit -m "Production deployment için hazır"
git push origin main
```

2. **Render.com'da hesap oluştur**

3. **"New Web Service" seç**

4. **GitHub repository'nizi bağlayın**

5. **Environment variables ekleyin:**
   - `SECRET_KEY`: Güvenli bir secret key
   - `JWT_SECRET_KEY`: JWT için secret key
   - `UYUMSOFT_USERNAME`: Uyumsoft kullanıcı adı
   - `UYUMSOFT_PASSWORD`: Uyumsoft şifresi
   - `UYUMSOFT_COMPANY_ID`: Şirket ID

6. **Deploy edin!**

## 📊 Özellikler

- Kullanıcı yönetimi ve yetkilendirme
- Departman bazlı izin sistemi
- Satış raporları ve analizler
- Görev yönetimi
- İade takibi
- Excel import/export

## 🛠️ Teknolojiler

- **Backend**: Flask, SQLAlchemy
- **Veritabanı**: SQLite (local), PostgreSQL (production)
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: Flask-Login

## 🔧 Konfigürasyon

`config.py` dosyasında tüm ayarları bulabilirsiniz.

## 📝 Notlar

- Production'da `debug=False` olmalı
- Veritabanı URL'i environment variable olarak ayarlanmalı
- Secret key'ler güvenli olmalı 