from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import db, bcrypt
from models import User
from functools import wraps

admin_bp = Blueprint('admin', __name__)

# Decorador para proteger rutas
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Debe iniciar sesión para acceder.", "warning")
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Ruta para registrar nuevos usuarios con verificación de contraseña."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role', 'user')
        
        # Verificación de contraseñas iguales
        if password != confirm_password:
            flash("Las contraseñas no coinciden. Inténtalo de nuevo.", "danger")
            return redirect(url_for('admin.register'))
        
        # Verificar si el usuario ya existe
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash("El nombre de usuario ya está en uso.", "danger")
            return redirect(url_for('admin.register'))
        
        # Encriptar contraseña y guardar
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password, role=role)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash("Cuenta creada exitosamente. Ahora puede iniciar sesión.", "success")
        return redirect(url_for('admin.login'))
        
    return render_template('register.html')

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Ruta para el inicio de sesión."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash(f"¡Bienvenido, {user.username}!", "success")
            return redirect(url_for('main.dashboard'))
        else:
            flash("Usuario o contraseña incorrectos.", "danger")
            
    return render_template('login.html')

@admin_bp.route('/logout')
def logout():
    """Cierra la sesión actual."""
    session.clear()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for('admin.login'))