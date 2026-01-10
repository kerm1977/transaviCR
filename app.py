# Archivo: app.py
from flask import Flask
from extensions import db, bcrypt

def create_app():
    """
    Configuración central de la aplicación Flask y registro de extensiones.
    """
    app = Flask(__name__)
    
    # Configuración del servidor y base de datos
    app.config['SECRET_KEY'] = 'transporte_busetas_secret_key_123'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar base de datos y encriptación
    db.init_app(app)
    bcrypt.init_app(app)

    # Registro de Blueprints
    from rutas import main_bp
    from users import users_bp
    from profile import profile_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(users_bp) 
    app.register_blueprint(profile_bp)

    # Inicialización de la base de datos y datos maestros
    with app.app_context():
        import models
        from users import User
        
        db.create_all()
        
        # --- CONFIGURACIÓN DE SUPERUSUARIOS ---
        # Lista de correos que serán administradores por defecto
        # Se crean automáticamente al iniciar la app si no existen
        superusers = [
            {'email': 'kenth1977@gmail.com', 'username': 'Kenth SuperAdmin'},
            {'email': 'lthikingcr@gmail.com', 'username': 'Lthiking SuperAdmin'}
        ]
        
        # Contraseña por defecto para los superusuarios (¡Cámbiala al entrar!)
        # Solicitada: CR129x7848n
        default_password = 'CR129x7848n' 
        hashed_pw = bcrypt.generate_password_hash(default_password).decode('utf-8')

        for super_data in superusers:
            user = User.query.filter_by(email=super_data['email']).first()
            
            if not user:
                # Crear superusuario si no existe
                new_admin = User(
                    username=super_data['username'],
                    email=super_data['email'],
                    role='admin', # Rol privilegiado
                    password=hashed_pw
                )
                db.session.add(new_admin)
                print(f"Superusuario creado: {super_data['email']}")
            else:
                # Si existe, asegurar que tenga rol de admin y actualizar password si es necesario (opcional)
                # Aquí solo forzamos el rol 'admin' para garantizar acceso
                if user.role != 'admin':
                    user.role = 'admin'
                    print(f"Rol de {super_data['email']} actualizado a admin.")
        
        # Commit de cambios (creación o actualización de roles)
        db.session.commit()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)