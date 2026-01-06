# Archivo: admin.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import db, bcrypt
from models import User
from functools import wraps

admin_bp = Blueprint('admin', __name__)

# Decorador para proteger rutas que requieren inicio de sesión
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
    """
    Procesa el registro de nuevos usuarios capturando username, email y password.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role', 'user')
        
        # Validar que las contraseñas coincidan
        if password != confirm_password:
            flash("Las contraseñas no coinciden. Inténtalo de nuevo.", "danger")
            return redirect(url_for('admin.register'))
        
        # Validar si el usuario o el email ya existen
        if User.query.filter_by(username=username).first():
            flash("El nombre de usuario ya está en uso.", "danger")
            return redirect(url_for('admin.register'))
            
        if User.query.filter_by(email=email).first():
            flash("Este correo electrónico ya está registrado.", "danger")
            return redirect(url_for('admin.register'))
        
        # Encriptar contraseña y crear usuario
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(
            username=username, 
            email=email, 
            password=hashed_password, 
            role=role
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Cuenta creada exitosamente. Ahora puedes iniciar sesión.", "success")
            return redirect(url_for('admin.login'))
        except Exception as e:
            db.session.rollback()
            flash("Ocurrió un error al crear la cuenta. Inténtalo más tarde.", "danger")
        
    return render_template('register.html')

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Inicia sesión validando el correo electrónico y la contraseña.
    """
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Buscar usuario por email
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash(f"¡Bienvenido de nuevo, {user.username}!", "success")
            return redirect(url_for('main.dashboard'))
        else:
            flash("Correo o contraseña incorrectos.", "danger")
            
    return render_template('login.html')

@admin_bp.route('/logout')
def logout():
    """
    Limpia la sesión del usuario.
    """
    session.clear()
    flash("Has cerrado sesión correctamente.", "info")
    return redirect(url_for('admin.login'))