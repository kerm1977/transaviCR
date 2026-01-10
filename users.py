# Archivo: users.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from extensions import db, bcrypt
from functools import wraps

# Definimos el Blueprint 'users'
users_bp = Blueprint('users', __name__)

# ==========================================
# 1. MODELO DE USUARIO (Base de Datos)
# ==========================================
class User(db.Model):
    """
    Modelo unificado para gestionar los usuarios del sistema.
    """
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False) # Aumentado a 200 para hashes largos
    # Roles sugeridos: 'admin', 'user', 'enterprise'
    role = db.Column(db.String(20), default='user') 

    def set_password(self, password_text):
        """Genera y guarda el hash de la contraseña."""
        self.password = bcrypt.generate_password_hash(password_text).decode('utf-8')

    def check_password(self, password_text):
        """Verifica si la contraseña coincide con el hash."""
        return bcrypt.check_password_hash(self.password, password_text)
    
    def __repr__(self):
        return f'<User {self.username}>'


# ==========================================
# 2. DECORADORES DE SEGURIDAD
# ==========================================
def login_required(f):
    """Restringe el acceso a usuarios logueados."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Debe iniciar sesión para acceder a esta sección.", "warning")
            return redirect(url_for('users.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Restringe el acceso solo a administradores."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            flash("Acceso denegado. Se requieren permisos de administrador.", "danger")
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# ==========================================
# 3. RUTAS DE AUTENTICACIÓN (Login/Registro)
# ==========================================
@users_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Registra un nuevo usuario en el sistema.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        # Permitimos que el form envíe un rol si es necesario, sino default 'user'
        role = request.form.get('role', 'user')
        
        # Validaciones básicas
        if password != confirm_password:
            flash("Las contraseñas no coinciden.", "danger")
            return redirect(url_for('users.register'))
        
        if User.query.filter_by(email=email).first():
            flash("El correo electrónico ya está registrado.", "danger")
            return redirect(url_for('users.register'))
            
        if User.query.filter_by(username=username).first():
            flash("El nombre de usuario ya existe.", "danger")
            return redirect(url_for('users.register'))
        
        # Crear usuario
        try:
            new_user = User(username=username, email=email, role=role)
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            flash("Cuenta creada exitosamente. Inicia sesión.", "success")
            return redirect(url_for('users.login'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al crear usuario: {str(e)}", "danger")
        
    return render_template('register.html')

@users_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Inicia sesión y crea la cookie de sesión.
    """
    # Si ya está logueado, redirigir al dashboard
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash(f"¡Bienvenido, {user.username}!", "success")
            return redirect(url_for('main.dashboard'))
        else:
            flash("Credenciales incorrectas.", "danger")
            
    return render_template('login.html')

@users_bp.route('/logout')
def logout():
    """
    Cierra la sesión del usuario.
    """
    session.clear()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for('users.login'))


# ==========================================
# 4. ADMINISTRACIÓN DE USUARIOS (CRUD)
# ==========================================

@users_bp.route('/users/manage')
@login_required
@admin_required
def manage_users():
    """
    Panel para ver todos los usuarios registrados (Solo Admin).
    Muestra la lista de usuarios usando el template 'users_list.html'.
    """
    users = User.query.all()
    # Usamos una plantilla específica para la lista para evitar errores de contexto
    return render_template('users_list.html', users=users)

@users_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """
    Elimina un usuario específico por ID.
    Evita que el admin se elimine a sí mismo.
    """
    if user_id == session.get('user_id'):
        flash("No puedes eliminar tu propia cuenta de administrador mientras estás logueado.", "warning")
        return redirect(url_for('main.dashboard'))

    user = User.query.get_or_404(user_id)
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f"Usuario {user.username} eliminado correctamente.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error al eliminar el usuario.", "danger")

    return redirect(url_for('users.manage_users'))

@users_bp.route('/users/change_role/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def change_role(user_id):
    """
    Cambia el rol de un usuario (ej: de 'user' a 'admin' o 'enterprise').
    """
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('new_role')
    
    if new_role in ['user', 'admin', 'enterprise']:
        # Evitar quitarse admin a uno mismo
        if user.id == session.get('user_id') and new_role != 'admin':
             flash("No puedes quitarte tus propios permisos de administrador.", "warning")
             return redirect(url_for('users.manage_users'))

        user.role = new_role
        db.session.commit()
        flash(f"Rol de {user.username} actualizado a {new_role}.", "success")
    else:
        flash("Rol no válido.", "danger")
        
    return redirect(url_for('users.manage_users'))