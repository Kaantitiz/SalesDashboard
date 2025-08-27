from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, UserRole, Department, DepartmentPermission
from auth import auth
from api import api
from config import Config
from sqlalchemy import text
import os
from datetime import datetime

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Veritabanı başlatma
    db.init_app(app)

    # Veritabanı başlatma ve migration
    with app.app_context():
        try:
            # Tabloları oluştur
            db.create_all()
            
            # PostgreSQL migration kontrolü
            if app.config.get('SQLALCHEMY_DATABASE_URI', '').startswith('postgresql://'):
                print("✅ PostgreSQL veritabanı kullanılıyor - veriler kalıcı olarak saklanacak")
                
                # Admin kullanıcısı kontrol et
                admin = User.query.filter_by(username='admin').first()
                if not admin:
                    from werkzeug.security import generate_password_hash
                    admin = User(
                        username='admin',
                        email='admin@company.com',
                        first_name='Admin',
                        last_name='User',
                        role=UserRole.ADMIN,
                        is_active=True,
                        password_hash=generate_password_hash('admin123')
                    )
                    db.session.add(admin)
                    db.session.commit()
                    print("👤 Admin kullanıcısı oluşturuldu: admin/admin123")
                
                # PostgreSQL için migration
                try:
                    # user tablosunda email sütununu nullable yap
                    db.session.execute(text("ALTER TABLE \"user\" ALTER COLUMN email DROP NOT NULL"))
                    db.session.commit()
                    print("[MIGRATION] PostgreSQL: user.email sütunu nullable yapıldı")
                except Exception as e:
                    print(f"[MIGRATION] PostgreSQL email migration hatası: {e}")
            else:
                print("🔧 SQLite veritabanı kullanılıyor (geliştirme ortamı)")
                
                # SQLite migration'ları (sadece geliştirme ortamında)
                # ÖNEMLİ: planning tablosunu düşürme kaldırıldı – veriler korunmalı
                # 'user' tablosunda department_role kolonu yoksa ekle
                try:
                    if app.config.get('SQLALCHEMY_DATABASE_URI', '').startswith('postgresql://'):
                        # PostgreSQL için sütun varlığını kontrol etme
                        result = db.session.execute(text(
                            "SELECT 1 FROM information_schema.columns WHERE table_name = 'user' AND column_name = 'department_role'"
                        )).scalar()
                        if not result:
                            db.session.execute(text("ALTER TABLE \"user\" ADD COLUMN department_role VARCHAR(100)"))
                            db.session.commit()
                            print("[MIGRATION] PostgreSQL: user.department_role sütunu eklendi")
                    else:
                        # SQLite için
                        info = db.session.execute(text("PRAGMA table_info('user')")).fetchall()
                        columns = [row[1] for row in info]
                        if 'department_role' not in columns:
                            db.session.execute(text("ALTER TABLE user ADD COLUMN department_role VARCHAR(100)"))
                            db.session.commit()
                            print("[MIGRATION] SQLite: user.department_role sütunu eklendi")
                except Exception as e:
                    print(f"[MIGRATION] department_role kontrol/ekleme hatası: {e}")
            # 'department' tablosunda default_role_title kolonu yoksa ekle
            try:
                if app.config.get('SQLALCHEMY_DATABASE_URI', '').startswith('postgresql://'):
                    # PostgreSQL için sütun varlığını kontrol etme
                    result = db.session.execute(text(
                        "SELECT 1 FROM information_schema.columns WHERE table_name = 'department' AND column_name = 'default_role_title'"
                    )).scalar()
                    if not result:
                        db.session.execute(text("ALTER TABLE department ADD COLUMN default_role_title VARCHAR(100)"))
                        db.session.commit()
                        print("[MIGRATION] PostgreSQL: department.default_role_title sütunu eklendi")
                else:
                    # SQLite için
                    info = db.session.execute(text("PRAGMA table_info('department')")).fetchall()
                    columns = [row[1] for row in info]
                    if 'default_role_title' not in columns:
                        db.session.execute(text("ALTER TABLE department ADD COLUMN default_role_title VARCHAR(100)"))
                        db.session.commit()
                        print("[MIGRATION] SQLite: department.default_role_title sütunu eklendi")
            except Exception as e:
                print(f"[MIGRATION] default_role_title kontrol/ekleme hatası: {e}")
            # 'department_permission' tablosunda actions kolonu yoksa ekle (granüler izinler)
            try:
                if app.config.get('SQLALCHEMY_DATABASE_URI', '').startswith('postgresql://'):
                    # PostgreSQL için sütun varlığını kontrol etme
                    result = db.session.execute(text(
                        "SELECT 1 FROM information_schema.columns WHERE table_name = 'department_permission' AND column_name = 'actions'"
                    )).scalar()
                    if not result:
                        db.session.execute(text("ALTER TABLE department_permission ADD COLUMN actions TEXT"))
                        db.session.commit()
                        print("[MIGRATION] PostgreSQL: department_permission.actions sütunu eklendi")
                else:
                    # SQLite için
                    info = db.session.execute(text("PRAGMA table_info('department_permission')")).fetchall()
                    columns = [row[1] for row in info]
                    if 'actions' not in columns:
                        db.session.execute(text("ALTER TABLE department_permission ADD COLUMN actions TEXT"))
                        db.session.commit()
                        print("[MIGRATION] SQLite: department_permission.actions sütunu eklendi")
            except Exception as e:
                print(f"[MIGRATION] department_permission.actions kontrol/ekleme hatası: {e}")
            # Satış Departmanı için varsayılan unvan ve kullanıcı unvanlarını ayarla
            try:
                sales_dept = Department.query.filter_by(name='Satış Departmanı').first()
                if sales_dept:
                    if not getattr(sales_dept, 'default_role_title', None):
                        sales_dept.default_role_title = 'Temsilci'
                    # Departmandaki kullanıcıların boş unvanlarını Temsilci yap
                    users_to_update = User.query.filter_by(department_id=sales_dept.id).all()
                    changed = False
                    for u in users_to_update:
                        if not u.department_role:
                            u.department_role = 'Temsilci'
                            changed = True
                    if changed:
                        db.session.commit()
                        print("[MIGRATION] Satış Departmanı kullanıcı unvanları 'Temsilci' olarak güncellendi")
                    else:
                        db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"[MIGRATION] satış departmanı unvan güncelleme hatası: {e}")
            # Teknik Dizel (Admin) departmanı oluştur ve tam yetki ver
            try:
                tech_dept = Department.query.filter_by(name='Teknik Dizel').first()
                if not tech_dept:
                    tech_dept = Department(name='Teknik Dizel', description='Admin departmanı', manager_id=None)
                    db.session.add(tech_dept)
                    db.session.commit()
                    print('[MIGRATION] Teknik Dizel departmanı oluşturuldu')
                # Admin kullanıcıları bu departmana ata (isteğe bağlı)
                admins = User.query.filter_by(role=UserRole.ADMIN).all()
                for adm in admins:
                    if adm.department_id != tech_dept.id:
                        adm.department_id = tech_dept.id
                db.session.commit()
                # Tüm modüller için tam yetki
                module_names = ['sales', 'tasks', 'returns', 'reports', 'user_management']
                for mod in module_names:
                    perm = DepartmentPermission.query.filter_by(department_id=tech_dept.id, module_name=mod).first()
                    if not perm:
                        perm = DepartmentPermission(
                            department_id=tech_dept.id,
                            module_name=mod,
                            can_view=True,
                            can_edit=True,
                            can_delete=True
                        )
                        db.session.add(perm)
                db.session.commit()
                print('[MIGRATION] Teknik Dizel yetkileri güncellendi')
            except Exception as e:
                db.session.rollback()
                print(f"[MIGRATION] Teknik Dizel oluşturma/izin hatası: {e}")
        except Exception as e:
            print(f"[MIGRATION] create_all hatası: {e}")
    
    # Login manager başlatma
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Bu sayfaya erişmek için giriş yapmalısınız.'
    
    @login_manager.user_loader
    def load_user(user_id):
        # Oturumda tutulan kullanıcı pasifleştirildiyse anında geçersiz sayılmalı
        try:
            u = User.query.get(int(user_id))
            if not u or not u.is_active:
                return None
            return u
        except Exception:
            return None

    @app.before_request
    def enforce_active_user():
        # Aktif olmayan kullanıcıların mevcut oturumu varsa kapat
        try:
            if current_user.is_authenticated and not current_user.is_active:
                logout_user()
        except Exception:
            pass
    
    # Blueprint'leri kaydet
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(api, url_prefix='/api')
    
    # Ana sayfa
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))
    
    # Giriş sayfası
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        # Güvenlik: kullanıcı tablosu kolonlarını garanti altına al
        try:
            info = db.session.execute(text("PRAGMA table_info('user')")).fetchall()
            columns = [row[1] for row in info]
            if 'department_role' not in columns:
                db.session.execute(text("ALTER TABLE user ADD COLUMN department_role VARCHAR(100)"))
                db.session.commit()
        except Exception:
            db.session.rollback()
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                if not user.is_active:
                    return render_template('login.html', error='Hesap aktif değil')
                
                login_user(user)
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error='Geçersiz kullanıcı adı veya şifre')
        
        return render_template('login.html')
    
    # Çıkış
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))
    
    # Dashboard
    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Sadece Admin ve Departman Yöneticisi dashboard görebilir
        if current_user.is_admin() or current_user.is_department_manager():
            return render_template('dashboard.html')
        # Diğer kullanıcıları kendi paneline yönlendir
        return redirect(url_for('user_panel'))
    
    # Admin paneli
    @app.route('/admin')
    @login_required
    def admin_panel():
        if not current_user.is_admin():
            return redirect(url_for('dashboard'))
        return render_template('admin.html')
    
    # Departman yöneticisi paneli (eski temsilci paneli yerine)
    @app.route('/representative')
    @login_required
    def representative_panel():
        # Geriye dönük URL: Departman yöneticisi ya da kullanıcılar dashboard'a gitsin
        if current_user.is_department_manager():
            return render_template('representative.html')
        return redirect(url_for('dashboard'))
    
    # Kullanıcı paneli
    @app.route('/user')
    @login_required
    def user_panel():
        # Tek şablon: user.html içinde departmana göre koşullu içerik
        return render_template('user.html')

    # Ayrı adlarla departman bazlı paneller (izin eşleştirme için)
    @app.route('/panel/sales')
    @login_required
    def panel_sales():
        # Erişim kontrolü: panel_sales izni
        if not current_user.has_permission('panel_sales', 'view') and not current_user.is_admin():
            return redirect(url_for('user_panel'))
        return render_template('panel_sales.html')

    @app.route('/panel/purchasing')
    @login_required
    def panel_purchasing():
        if not current_user.has_permission('panel_purchasing', 'view') and not current_user.is_admin():
            return redirect(url_for('user_panel'))
        return render_template('panel_purchasing.html')

    # Departman Yöneticisi Paneli
    @app.route('/panel/department')
    @login_required
    def panel_department():
        if not (current_user.is_admin() or current_user.is_department_manager()):
            return redirect(url_for('user_panel'))
        return render_template('panel_department.html')
    
    # Admin planlama sayfası – kapatıldı
    @app.route('/admin/planning')
    @login_required
    def admin_planning_page():
        return redirect(url_for('dashboard'))
    
    # Departman kullanıcısı planlama sayfası – kapatıldı
    @app.route('/representative/planning')
    @login_required
    def representative_planning_page():
        return redirect(url_for('dashboard'))
    
    # Eski genel planlama sayfası – kapatıldı
    @app.route('/planning')
    @login_required
    def planning_page():
        return redirect(url_for('dashboard'))

    # Yeni Görevler sayfası
    @app.route('/tasks')
    @login_required
    def tasks_page():
        return render_template('tasks.html')
    
    # Planlama Arşivi sayfası
    @app.route('/planning-archive')
    @login_required
    def planning_archive_page():
        return render_template('planning_archive.html')

    # Kullanıcı yönetimi sayfası
    @app.route('/user-management')
    @login_required
    def user_management():
        if not current_user.is_admin():
            return redirect(url_for('dashboard'))
        return render_template('user_management.html')
    
    # Departman yönetimi sayfası
    @app.route('/department-management')
    @login_required
    def department_management():
        if not current_user.is_admin():
            return redirect(url_for('dashboard'))
        return render_template('department_management.html')
    
    # Profil sayfası
    @app.route('/profile')
    @login_required
    def profile():
        return render_template('profile.html')

    # Manuel DB migration endpoint (geçici)
    @app.route('/db-migrate')
    def db_migrate():
        try:
            # 'user' tablosunda department_role kolonu yoksa ekle
            info = db.session.execute(text("PRAGMA table_info('user')")).fetchall()
            columns = [row[1] for row in info]
            changed = False
            if 'department_role' not in columns:
                db.session.execute(text("ALTER TABLE user ADD COLUMN department_role VARCHAR(100)"))
                changed = True
            db.session.commit()
            return jsonify({'message': 'Migration OK', 'changed': changed}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/db-info')
    def db_info():
        try:
            # Aktif veritabanı dosyası
            db_list = db.session.execute(text("PRAGMA database_list")).fetchall()
            # user tablosu kolonları
            info = db.session.execute(text("PRAGMA table_info('user')")).fetchall()
            columns = [row[1] for row in info]
            return jsonify({
                'database_list': [tuple(row) for row in db_list],
                'user_columns': columns,
                'uri': app.config.get('SQLALCHEMY_DATABASE_URI')
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Veritabanı oluşturma
    @app.route('/init-db')
    def init_db():
        with app.app_context():
            db.create_all()
            # Basit migration: user.department_role kolonu ekle (yoksa)
            try:
                info = db.session.execute(text("PRAGMA table_info('user')")).fetchall()
                columns = [row[1] for row in info]
                if 'department_role' not in columns:
                    db.session.execute(text("ALTER TABLE user ADD COLUMN department_role VARCHAR(100)"))
                    db.session.commit()
                    print("department_role sütunu eklendi")
            except Exception as e:
                print(f"department_role sütunu kontrol/ekleme hatası: {e}")
            
            # Admin kullanıcısı oluştur
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@company.com',
                    first_name='Admin',
                    last_name='User',
                    role=UserRole.ADMIN
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("Admin kullanıcısı oluşturuldu: admin/admin123")
            
            # Satış Departmanı oluştur
            sales_dept = Department.query.filter_by(name='Satış Departmanı').first()
            if not sales_dept:
                sales_dept = Department(
                    name='Satış Departmanı',
                    description='Satış ve pazarlama işlemleri'
                )
                db.session.add(sales_dept)
                db.session.commit()
                print("Satış Departmanı oluşturuldu")
            
            # Örnek departman yöneticisi oluştur
            manager = User.query.filter_by(username='manager1').first()
            if not manager:
                manager = User(
                    username='manager1',
                    email='manager1@company.com',
                    first_name='Departman',
                    last_name='Yöneticisi',
                    role=UserRole.DEPARTMENT_MANAGER,
                    phone='0555 123 4567',
                    region='İstanbul',
                    department_id=sales_dept.id
                )
                manager.set_password('manager123')
                db.session.add(manager)
                db.session.commit()
                print("Örnek departman yöneticisi oluşturuldu: manager1/manager123")
            
            # Örnek kullanıcı oluştur
            user = User.query.filter_by(username='user1').first()
            if not user:
                user = User(
                    username='user1',
                    email='user1@company.com',
                    first_name='Mehmet',
                    last_name='Demir',
                    role=UserRole.USER,
                    department_id=sales_dept.id
                )
                user.set_password('user123')
                db.session.add(user)
                db.session.commit()
                print("Örnek kullanıcı oluşturuldu: user1/user123")
            
            # Satış Departmanı için izinler oluştur
            permissions = [
                {'module_name': 'sales', 'can_view': True, 'can_edit': True, 'can_delete': False},
                {'module_name': 'returns', 'can_view': True, 'can_edit': True, 'can_delete': False},
                {'module_name': 'tasks', 'can_view': True, 'can_edit': True, 'can_delete': False},
                {'module_name': 'reports', 'can_view': True, 'can_edit': False, 'can_delete': False},
                {'module_name': 'user_management', 'can_view': False, 'can_edit': False, 'can_delete': False}
            ]
            
            for perm_data in permissions:
                existing_perm = DepartmentPermission.query.filter_by(
                    department_id=sales_dept.id,
                    module_name=perm_data['module_name']
                ).first()
                
                if not existing_perm:
                    permission = DepartmentPermission(
                        department_id=sales_dept.id,
                        module_name=perm_data['module_name'],
                        can_view=perm_data['can_view'],
                        can_edit=perm_data['can_edit'],
                        can_delete=perm_data['can_delete']
                    )
                    db.session.add(permission)
            
            db.session.commit()
            print("Satış Departmanı izinleri oluşturuldu")
            
            return jsonify({'message': 'Veritabanı başlatıldı'})
    
    @app.route('/debug-upload')
    def debug_upload():
        return send_file('debug_frontend.html')
    
    # Legacy debug route removed

    @app.route('/test')
    def test_page():
        return send_from_directory('.', 'test_api.html')

    return app

if __name__ == '__main__':
    app = create_app()
    
    # Upload klasörü oluştur
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Production'da debug=False olmalı
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 