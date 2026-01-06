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
    from admin import admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    # Inicialización de la base de datos y datos maestros
    with app.app_context():
        import models
        db.create_all()
        
        from models import User
        # Verificar si existe el administrador del sistema
        if not User.query.filter_by(username='admin').first():
            hashed_pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin = User(
                username='admin', 
                email='admin@sistema.com', 
                password=hashed_pw, 
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)