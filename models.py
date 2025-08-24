from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import enum

db = SQLAlchemy()

class UserRole(enum.Enum):
    ADMIN = "admin"
    REPRESENTATIVE = "representative"
    USER = "user"
    DEPARTMENT_MANAGER = "department_manager"

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Opsiyonel: Departman içi unvan için varsayılan başlık
    default_role_title = db.Column(db.String(100), nullable=True)
    
    # İlişkiler
    manager = db.relationship('User', foreign_keys=[manager_id], backref='managed_departments')
    users = db.relationship('User', foreign_keys='User.department_id', backref='department')
    permissions = db.relationship('DepartmentPermission', backref='department', lazy=True, cascade='all, delete-orphan')

class DepartmentPermission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    module_name = db.Column(db.String(100), nullable=False)  # 'sales', 'planning', 'reports', etc.
    can_view = db.Column(db.Boolean, default=True)
    can_edit = db.Column(db.Boolean, default=False)
    can_delete = db.Column(db.Boolean, default=False)
    # Granüler izinler için JSON (string olarak saklanır). Örn: {"assign": true, "export": false}
    actions = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('department_id', 'module_name', name='unique_department_permission'),)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.USER)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Departman ilişkisi
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    # Kullanıcının departman içindeki rol/unvanı (ör. Temsilci)
    department_role = db.Column(db.String(100), nullable=True)
    
    # Temsilci için ek alanlar
    representative_code = db.Column(db.String(20), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    
    # İlişkiler
    targets = db.relationship('Target', backref='user', lazy=True)
    sales = db.relationship('Sales', backref='representative', lazy=True)
    returns = db.relationship('Returns', backref='representative', lazy=True)
    plans = db.relationship('Planning', backref='representative', lazy=True)
    activity_logs = db.relationship('ActivityLog', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        first = self.first_name or ""
        last = self.last_name or ""
        full_name = f"{first} {last}".strip()
        return full_name if full_name else "Bilinmeyen Temsilci"
    
    def is_admin(self):
        return self.role == UserRole.ADMIN
    
    def is_representative(self):
        return self.role == UserRole.REPRESENTATIVE
    
    def is_department_manager(self):
        return self.role == UserRole.DEPARTMENT_MANAGER
    
    def is_department_manager_of(self, department_id):
        """Bu kullanıcının belirtilen departmanın yöneticisi olup olmadığını kontrol eder"""
        return self.role == UserRole.DEPARTMENT_MANAGER and self.department_id == department_id
    
    def has_permission(self, module_name, permission_type='view'):
        """Kullanıcının belirli bir modül için yetkisi olup olmadığını kontrol eder"""
        if self.is_admin():
            return True
        
        if not self.department_id:
            return False
        
        # Modül adını normalize et
        normalized_module = (module_name or '').lower()
        # Önce departman bazlı wildcard ("*") izni var mı?
        wildcard = DepartmentPermission.query.filter_by(
            department_id=self.department_id,
            module_name='*'
        ).first()
        if wildcard:
            # Granüler actions varsa onu kontrol et, yoksa can_* bayrakları tüm modüller için izin say
            try:
                import json
                if wildcard.actions:
                    data = json.loads(wildcard.actions)
                    if isinstance(data, dict) and (data.get('all_access') or data.get(permission_type) is True):
                        return True
            except Exception:
                pass
            if permission_type == 'view' and wildcard.can_view:
                return True
            if permission_type == 'edit' and wildcard.can_edit:
                return True
            if permission_type == 'delete' and wildcard.can_delete:
                return True
        
        permission = DepartmentPermission.query.filter_by(
            department_id=self.department_id,
            module_name=normalized_module
        ).first()
        
        if not permission:
            return False
        # Önce granüler actions kontrolü
        try:
            import json
            if permission.actions:
                data = json.loads(permission.actions)
                if isinstance(data, dict) and permission_type in data:
                    return bool(data.get(permission_type))
        except Exception:
            pass
        # Geriye dönük uyumluluk
        if permission_type == 'view':
            return permission.can_view
        elif permission_type == 'edit':
            return permission.can_edit
        elif permission_type == 'delete':
            return permission.can_delete
        return False

class Planning(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    representative_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    yesterday_activities = db.Column(db.Text, nullable=True)  # Dün yapılanlar
    today_plan = db.Column(db.Text, nullable=True)  # Bugün yapılacaklar
    challenges = db.Column(db.Text, nullable=True)  # Karşılaşılan zorluklar
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('representative_id', 'date', name='unique_planning_per_day'),)
    
    def can_edit(self):
        """24 saat içinde düzenlenebilir"""
        return datetime.utcnow() - self.created_at < timedelta(hours=24)

class PlanningSnapshot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    representative_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    yesterday_activities = db.Column(db.Text, nullable=True)
    today_plan = db.Column(db.Text, nullable=True)
    challenges = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    representative = db.relationship('User')

class Target(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'year', 'month', name='unique_target'),)

class Sales(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    representative_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    product_group = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    net_price = db.Column(db.Float, nullable=False)
    customer_name = db.Column(db.String(200), nullable=True)  # Müşteri adı
    customer_code = db.Column(db.String(50), nullable=True)   # Müşteri kodu
    # JSON'dan gelen orijinal alanlar
    original_quantity = db.Column(db.String(20), nullable=True)  # ADET alanından
    original_date = db.Column(db.String(20), nullable=True)      # TARIH alanından
    original_product_group = db.Column(db.String(100), nullable=True)  # URUN_ANA_GRUP alanından
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Returns(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    representative_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    product_group = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    net_price = db.Column(db.Float, nullable=False)
    return_reason = db.Column(db.String(200), nullable=True)
    customer_name = db.Column(db.String(200), nullable=True)  # Müşteri adı
    customer_code = db.Column(db.String(50), nullable=True)   # Müşteri kodu
    # JSON'dan gelen orijinal alanlar
    original_quantity = db.Column(db.String(20), nullable=True)  # ADET alanından
    original_date = db.Column(db.String(20), nullable=True)      # TARIH alanından
    original_product_group = db.Column(db.String(100), nullable=True)  # URUN_ANA_GRUP alanından
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    product_group = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User') 

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    title = db.Column(db.String(200), nullable=True)
    message = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(255), nullable=True)
    entity_type = db.Column(db.String(50), nullable=True)  # e.g., 'task'
    entity_id = db.Column(db.Integer, nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)

    to_user = db.relationship('User', foreign_keys=[to_user_id])
    created_by = db.relationship('User', foreign_keys=[created_by_id])

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Ownership and scope
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    assigned_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Status/Priority
    status = db.Column(db.String(50), default='pending', nullable=False)
    priority = db.Column(db.String(50), default='normal', nullable=False)

    # Dates
    start_date = db.Column(db.Date, nullable=True)
    due_date = db.Column(db.Date, nullable=True)

    # Recurrence
    is_recurring = db.Column(db.Boolean, default=False, nullable=False)
    recurrence = db.Column(db.String(50), default='none', nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assigned_by = db.relationship('User', foreign_keys=[assigned_by_id], lazy=True)
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], lazy=True)
    created_by = db.relationship('User', foreign_keys=[created_by_id], lazy=True)
    department = db.relationship('Department', foreign_keys=[department_id], lazy=True)

class TaskComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    task = db.relationship('Task', backref=db.backref('comments', lazy=True, cascade='all, delete-orphan'))
    user = db.relationship('User')