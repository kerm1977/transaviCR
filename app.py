import os
from flask import Flask
from extensions import db, bcrypt

def create_app():
    """
    Factory function para crear y configurar la instancia de la aplicación Flask.
    """
    app = Flask(__name__)
    
    # Configuración de la aplicación
    app.config['SECRET_KEY'] = 'transporte_busetas_secret_key_123'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar las extensiones vinculándolas a la app
    db.init_app(app)
    bcrypt.init_app(app)

    # Importar y registrar el Blueprint de las rutas
    from rutas import main_bp
    app.register_blueprint(main_bp)

    # Crear la base de datos y el usuario administrador inicial dentro del contexto
    with app.app_context():
        import models  # Carga los modelos para que SQLAlchemy los reconozca
        db.create_all()
        
        from models import User
        if not User.query.filter_by(username='admin').first():
            hashed_pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin = User(username='admin', password=hashed_pw, role='admin')
            db.session.add(admin)
            db.session.commit()

    return app

if __name__ == '__main__':
    # Ejecución del servidor
    app = create_app()
    app.run(debug=True, port=5000)