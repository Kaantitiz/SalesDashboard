from flask import Blueprint, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from models import db, User, UserRole, ActivityLog, Department, DepartmentPermission
from datetime import datetime
import jwt
from functools import wraps

auth = Blueprint('auth', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            return jsonify({'error': 'Admin yetkisi gerekli'}), 403
        return f(*args, **kwargs)
    return decorated_function

def department_manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_department_manager():
            return jsonify({'error': 'Departman yöneticisi yetkisi gerekli'}), 403
        return f(*args, **kwargs)
    return decorated_function

def representative_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Backward compatibility: Treat as a user who has sales permission
        if not current_user.is_authenticated or not current_user.has_permission('sales', 'view'):
            return jsonify({'error': 'Bu işlem için satış modülünde yetki gerekli'}), 403
        return f(*args, **kwargs)
    return decorated_function

def permission_required(module_name, permission_type='view'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Giriş yapmanız gerekiyor'}), 401
            
            if not current_user.has_permission(module_name, permission_type):
                return jsonify({'error': f'{module_name} modülü için {permission_type} yetkisi gerekli'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def action_required(module_name, action_name):
    """Granüler module action kontrolü. Örn: action_required('tasks','assign')"""
    return permission_required(module_name, action_name)

def admin_or_department_manager_required(f):
    """Allows access to Admins and Department Managers only."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Giriş yapmanız gerekiyor'}), 401
        if not (current_user.is_admin() or current_user.is_department_manager()):
            return jsonify({'error': 'Admin veya departman yöneticisi yetkisi gerekli'}), 403
        return f(*args, **kwargs)
    return decorated_function

def log_activity(action, description=None):
    """Kullanıcı aktivitelerini loglar"""
    if current_user.is_authenticated:
        log = ActivityLog(
            user_id=current_user.id,
            action=action,
            description=description,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()

def get_scoped_user_ids():
    """Returns a list of user IDs that the current_user is allowed to access.
    - Admin: returns None (means no restriction)
    - Department Manager: all users in their department
    - Regular User: only themselves
    """
    if not current_user.is_authenticated:
        return []
    if current_user.is_admin():
        return None
    if current_user.is_department_manager():
        if not current_user.department_id:
            return []
        users = User.query.filter_by(department_id=current_user.department_id).with_entities(User.id).all()
        return [u.id for u in users]
    return [current_user.id]

def is_user_in_scope(user_id: int) -> bool:
    """Checks whether the given user_id is within current_user's access scope."""
    scoped_ids = get_scoped_user_ids()
    if scoped_ids is None:
        return True
    return user_id in scoped_ids

@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Kullanıcı adı ve şifre gerekli'}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password):
        # Pasif veya silinmiş kullanıcı giriş yapamaz
        if not user.is_active:
            return jsonify({'error': 'Hesap aktif değil'}), 403
        
        login_user(user)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        log_activity('login', f'Kullanıcı giriş yaptı: {username}')
        
        # JWT token oluştur
        token = jwt.encode(
            {
                'user_id': user.id,
                'username': user.username,
                'role': user.role.value,
                'exp': datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
            },
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        
        return jsonify({
            'message': 'Giriş başarılı',
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role.value,
                'full_name': user.get_full_name()
            }
        }), 200
    
    return jsonify({'error': 'Geçersiz kullanıcı adı veya şifre'}), 401

@auth.route('/logout', methods=['POST'])
@login_required
def logout():
    log_activity('logout', f'Kullanıcı çıkış yaptı: {current_user.username}')
    logout_user()
    return jsonify({'message': 'Çıkış başarılı'}), 200

@auth.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    required_fields = ['username', 'email', 'password', 'first_name', 'last_name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} alanı gerekli'}), 400
    
    # Kullanıcı adı ve email kontrolü
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Bu kullanıcı adı zaten kullanılıyor'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Bu email adresi zaten kullanılıyor'}), 400
    
    # Yeni kullanıcı oluştur
    user = User(
        username=data['username'],
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        role=UserRole.USER  # Varsayılan rol
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    log_activity('register', f'Yeni kullanıcı kaydı: {user.username}')
    
    return jsonify({'message': 'Kayıt başarılı'}), 201

@auth.route('/profile', methods=['GET'])
@login_required
def get_profile():
    # DM/Admin başka bir kullanıcıyı görüntüleyebilsin
    view_user_id = request.args.get('user_id', type=int)
    user = current_user
    if view_user_id and (current_user.is_admin() or is_user_in_scope(view_user_id)):
        user = User.query.get_or_404(view_user_id)
    
    department_name = None
    if user.department_id:
        department = Department.query.get(user.department_id)
        if department:
            department_name = department.name
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role.value,
        'full_name': user.get_full_name(),
        'first_name': user.first_name,
        'last_name': user.last_name,
        'representative_code': user.representative_code,
        'phone': user.phone,
        'region': user.region,
        'department_name': department_name,
        'is_active': user.is_active,
        'created_at': user.created_at.isoformat(),
        'last_login': user.last_login.isoformat() if user.last_login else None
    }), 200

@auth.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    data = request.get_json()
    
    # Güncellenebilir alanlar
    updatable_fields = ['first_name', 'last_name', 'phone', 'region']
    
    for field in updatable_fields:
        if field in data:
            setattr(current_user, field, data[field])
    # Kullanıcı adı değişikliği
    if 'username' in data:
        new_username = (data['username'] or '').strip()
        if not new_username:
            return jsonify({'error': 'Kullanıcı adı boş olamaz'}), 400
        # Aynıysa atla
        if new_username != current_user.username:
            # Kullanılıyor mu?
            if User.query.filter_by(username=new_username).first():
                return jsonify({'error': 'Bu kullanıcı adı zaten kullanılıyor'}), 400
            current_user.username = new_username
    
    # Şifre değişikliği
    if 'password' in data and data['password']:
        current_user.set_password(data['password'])
    
    db.session.commit()
    
    log_activity('profile_update', 'Profil güncellendi')
    
    return jsonify({'message': 'Profil güncellendi'}), 200

@auth.route('/users', methods=['GET'])
@admin_required
def get_users():
    """Admin: Tüm kullanıcıları listele"""
    users = User.query.all()
    return jsonify({
        'users': [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role.value,
            'full_name': user.get_full_name(),
            'is_active': user.is_active,
            'department_id': user.department_id,
            'department_role': user.department_role,
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None
        } for user in users]
    }), 200

@auth.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """Admin: Kullanıcı güncelle"""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    # Güncellenebilir alanlar
    if 'role' in data:
        # Sistem rolleri üç tanedir: admin, department_manager, user
        try:
            user.role = UserRole(data['role'])
        except Exception:
            return jsonify({'error': 'Geçersiz sistem rolü'}), 400
    
    if 'is_active' in data:
        user.is_active = data['is_active']
    
    if 'representative_code' in data:
        user.representative_code = data['representative_code']

    # Departman içi rol ismi (departman yöneticisi yetkisinde yönetilebilir)
    if 'department_role' in data:
        if current_user.is_admin() or current_user.is_department_manager_of(user.department_id):
            user.department_role = data['department_role']
        else:
            return jsonify({'error': 'Departman rolü atamak için yetkiniz yok'}), 403
    
    db.session.commit()
    
    log_activity('user_update', f'Kullanıcı güncellendi: {user.username}')
    
    return jsonify({'message': 'Kullanıcı güncellendi'}), 200

@auth.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Admin: Kullanıcı sil"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        return jsonify({'error': 'Kendinizi silemezsiniz'}), 400
    
    # Sert silme yerine pasif hale getir + kişisel verileri minimalleştir (güvenli soft delete)
    try:
        user.is_active = False
        # Kimlik bilgilerini anonimleştir
        anon_suffix = f"_deleted_{user.id}"
        user.username = (user.username or 'user') + anon_suffix
        user.email = None
        user.representative_code = None
        # Oturum ve bağlı kayıtlar kullanıcısız kalabilir, ancak giriş engellenir
        db.session.commit()
    except Exception:
        db.session.rollback()
        # Fallback: hard delete (isteğe bağlı)
        try:
            db.session.delete(user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({'error': 'Kullanıcı silinemedi'}), 500
    
    log_activity('user_delete', f'Kullanıcı silindi: {user.username}')
    
    return jsonify({'message': 'Kullanıcı silindi'}), 200 

@auth.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Kullanıcının kendi şifresini değiştirmesi"""
    data = request.get_json()
    
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'error': 'Mevcut şifre ve yeni şifre gerekli'}), 400
    
    if not current_user.check_password(current_password):
        return jsonify({'error': 'Mevcut şifre yanlış'}), 400
    
    if len(new_password) < 6:
        return jsonify({'error': 'Yeni şifre en az 6 karakter olmalıdır'}), 400
    
    current_user.set_password(new_password)
    db.session.commit()
    
    log_activity('password_change', 'Şifre değiştirildi')
    
    return jsonify({'message': 'Şifre başarıyla değiştirildi'}), 200

@auth.route('/departments', methods=['GET'])
@admin_required
def get_departments():
    """Admin: Tüm departmanları listele"""
    departments = Department.query.all()
    return jsonify({
        'departments': [{
            'id': dept.id,
            'name': dept.name,
            'description': dept.description,
            'default_role_title': getattr(dept, 'default_role_title', None),
            'manager_id': dept.manager_id,
            'manager_name': dept.manager.get_full_name() if dept.manager else None,
            'is_active': dept.is_active,
            'user_count': len(dept.users),
            'created_at': dept.created_at.isoformat()
        } for dept in departments]
    }), 200

@auth.route('/departments', methods=['POST'])
@admin_required
def create_department():
    """Admin: Yeni departman oluştur"""
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'error': 'Departman adı gerekli'}), 400
    
    if Department.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Bu departman adı zaten kullanılıyor'}), 400
    
    department = Department(
        name=data['name'],
        description=data.get('description', ''),
        default_role_title=data.get('default_role_title'),
        manager_id=data.get('manager_id')
    )
    
    db.session.add(department)
    db.session.commit()
    # Eğer manager_id verildiyse kullanıcının rolünü DEPARTMENT_MANAGER yap
    try:
        if department.manager_id:
            new_manager = User.query.get(department.manager_id)
            if new_manager and new_manager.role != UserRole.ADMIN:
                new_manager.role = UserRole.DEPARTMENT_MANAGER
                # Yöneticinin departmanı farklıysa eşitle
                if new_manager.department_id != department.id:
                    new_manager.department_id = department.id
                db.session.commit()
    except Exception:
        db.session.rollback()
    
    log_activity('department_create', f'Departman oluşturuldu: {department.name}')
    
    return jsonify({
        'message': 'Departman oluşturuldu',
        'department': {
            'id': department.id,
            'name': department.name,
            'description': department.description,
            'default_role_title': department.default_role_title,
            'manager_id': department.manager_id
        }
    }), 201

@auth.route('/departments/<int:dept_id>', methods=['PUT'])
@admin_required
def update_department(dept_id):
    """Admin: Departman güncelle"""
    department = Department.query.get_or_404(dept_id)
    data = request.get_json()
    
    if 'name' in data and data['name'] != department.name:
        if Department.query.filter_by(name=data['name']).first():
            return jsonify({'error': 'Bu departman adı zaten kullanılıyor'}), 400
        department.name = data['name']
    
    if 'description' in data:
        department.description = data['description']
    if 'default_role_title' in data:
        department.default_role_title = data['default_role_title']
    
    if 'manager_id' in data:
        # Eski-yeni yönetici rolleri güncelle
        old_manager_id = department.manager_id
        new_manager_id = data['manager_id']
        department.manager_id = new_manager_id
        try:
            # Eski yöneticiyi gerekirse düşür
            if old_manager_id and old_manager_id != new_manager_id:
                old_manager = User.query.get(old_manager_id)
                if old_manager and old_manager.role == UserRole.DEPARTMENT_MANAGER:
                    # Başka departman yöneticiliği yoksa user yap
                    other_count = Department.query.filter(Department.manager_id == old_manager.id, Department.id != department.id).count()
                    if other_count == 0:
                        old_manager.role = UserRole.USER
            # Yeni yöneticiyi ata
            if new_manager_id:
                new_manager = User.query.get(new_manager_id)
                if new_manager and new_manager.role != UserRole.ADMIN:
                    new_manager.role = UserRole.DEPARTMENT_MANAGER
                    if new_manager.department_id != department.id:
                        new_manager.department_id = department.id
        except Exception:
            db.session.rollback()
    
    if 'is_active' in data:
        department.is_active = data['is_active']
    
    db.session.commit()
    
    log_activity('department_update', f'Departman güncellendi: {department.name}')
    
    return jsonify({'message': 'Departman güncellendi'}), 200

@auth.route('/departments/<int:dept_id>/permissions', methods=['GET'])
@admin_required
def get_department_permissions(dept_id):
    """Admin: Departman izinlerini getir"""
    department = Department.query.get_or_404(dept_id)
    permissions = DepartmentPermission.query.filter_by(department_id=dept_id).all()
    
    return jsonify({
        'permissions': [{
            'id': perm.id,
            'module_name': perm.module_name,
            'can_view': perm.can_view,
            'can_edit': perm.can_edit,
            'can_delete': perm.can_delete,
            'actions': getattr(perm, 'actions', None)
        } for perm in permissions]
    }), 200

@auth.route('/departments/<int:dept_id>/permissions', methods=['POST'])
@admin_required
def set_department_permissions(dept_id):
    """Admin: Departman izinlerini ayarla"""
    department = Department.query.get_or_404(dept_id)
    data = request.get_json()
    
    # Mevcut izinleri temizle
    DepartmentPermission.query.filter_by(department_id=dept_id).delete()
    
    # Yeni izinleri ekle (granüler actions destekli)
    from json import dumps
    for permission_data in data.get('permissions', []):
        module_name = (permission_data.get('module_name') or '').lower()
        permission = DepartmentPermission(
            department_id=dept_id,
            module_name=module_name,
            can_view=permission_data.get('can_view', True),
            can_edit=permission_data.get('can_edit', False),
            can_delete=permission_data.get('can_delete', False),
            actions=dumps(permission_data.get('actions', {})) if permission_data.get('actions') else None
        )
        db.session.add(permission)
    
    db.session.commit()
    
    log_activity('department_permissions_update', f'Departman izinleri güncellendi: {department.name}')
    
    return jsonify({'message': 'Departman izinleri güncellendi'}), 200

@auth.route('/departments/<int:dept_id>/users', methods=['GET'])
@admin_required
def get_department_users(dept_id):
    """Admin: Departmandaki kullanıcıları listele"""
    department = Department.query.get_or_404(dept_id)
    
    return jsonify({
        'users': [{
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name(),
            'email': user.email,
            'representative_code': user.representative_code,
            'role': user.role.value,
            'department_role': user.department_role,
            'is_active': user.is_active,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'created_at': user.created_at.isoformat() if user.created_at else None
        } for user in department.users]
    }), 200

@auth.route('/departments/<int:dept_id>/users', methods=['POST'])
@admin_required
def add_user_to_department(dept_id):
    """Admin: Kullanıcıyı departmana ekle"""
    department = Department.query.get_or_404(dept_id)
    data = request.get_json()
    
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'Kullanıcı ID gerekli'}), 400
    
    user = User.query.get_or_404(user_id)
    user.department_id = dept_id
    # DM bu kullanıcıya departman içi rol ismi atamışsa uygula
    if data.get('department_role'):
        user.department_role = data['department_role']
    db.session.commit()
    
    log_activity('user_department_add', f'Kullanıcı departmana eklendi: {user.username} -> {department.name}')
    
    return jsonify({'message': 'Kullanıcı departmana eklendi'}), 200

@auth.route('/departments/<int:dept_id>/users/<int:user_id>', methods=['DELETE'])
@admin_required
def remove_user_from_department(dept_id, user_id):
    """Admin: Kullanıcıyı departmandan çıkar"""
    department = Department.query.get_or_404(dept_id)
    user = User.query.get_or_404(user_id)
    
    if user.department_id != dept_id:
        return jsonify({'error': 'Kullanıcı bu departmanda değil'}), 400
    
    user.department_id = None
    db.session.commit()
    
    log_activity('user_department_remove', f'Kullanıcı departmandan çıkarıldı: {user.username} -> {department.name}')
    
    return jsonify({'message': 'Kullanıcı departmandan çıkarıldı'}), 200

@auth.route('/my-department', methods=['GET'])
@login_required
def get_my_department():
    """Kullanıcının kendi departmanını getir"""
    if not current_user.department_id:
        return jsonify({'error': 'Kullanıcı herhangi bir departmanda değil'}), 404
    
    department = Department.query.get(current_user.department_id)
    if not department:
        return jsonify({'error': 'Departman bulunamadı'}), 404
    
    return jsonify({
        'department': {
            'id': department.id,
            'name': department.name,
            'description': department.description,
            'manager_id': department.manager_id,
            'manager_name': department.manager.get_full_name() if department.manager else None,
            'is_active': department.is_active
        }
    }), 200

@auth.route('/departments/<int:dept_id>', methods=['GET'])
@admin_required
def get_department(dept_id):
    """Admin: Departman bilgilerini getir"""
    department = Department.query.get_or_404(dept_id)
    
    return jsonify({
        'department': {
            'id': department.id,
            'name': department.name,
            'description': department.description,
            'default_role_title': getattr(department, 'default_role_title', None),
            'manager_id': department.manager_id,
            'manager_name': department.manager.get_full_name() if department.manager else None,
            'is_active': department.is_active,
            'created_at': department.created_at.isoformat()
        }
    }), 200 