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

    # Registro de Blueprints para modularizar rutas
    from rutas import main_bp
    # CAMBIO: Importamos users_bp en lugar de admin_bp
    from users import users_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(users_bp) # Registramos el nuevo blueprint de usuarios

    # Inicialización de la base de datos y datos maestros
    with app.app_context():
        # Importamos modelos para asegurar que SQLAlchemy los reconozca al crear tablas
        import models
        # CAMBIO: Importamos User desde users, no desde models
        from users import User
        
        db.create_all()
        
        # Verificar si existe el administrador del sistema
        if not User.query.filter_by(username='admin').first():
            # Crear admin por defecto si no existe
            # Usamos el método set_password del modelo User si prefieres, 
            # o lo hacemos manual como estaba antes para asegurar compatibilidad.
            hashed_pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
            
            admin = User(
                username='admin', 
                email='admin@sistema.com', 
                role='admin'
            )
            # Asignamos el password hasheado manualmente
            admin.password = hashed_pw
            
            db.session.add(admin)
            db.session.commit()
            print("Usuario admin creado: admin / admin123")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)