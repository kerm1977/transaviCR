from flask import Flask
from extensions import db, bcrypt

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'transporte_busetas_secret_key_123'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 1. Inicializar extensiones
    db.init_app(app)
    bcrypt.init_app(app)

    # 2. IMPORTAR Y REGISTRAR BLUEPRINTS
    from rutas import main_bp
    from admin import admin_bp  # <--- IMPORTANTE: Importar el Blueprint de admin
    
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp) # <--- IMPORTANTE: Registrar el Blueprint de admin

    # 3. Configurar base de datos
    with app.app_context():
        import models
        db.create_all()
        
        from models import User
        if not User.query.filter_by(username='admin').first():
            hashed_pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin = User(username='admin', password=hashed_pw, role='admin')
            db.session.add(admin)
            db.session.commit()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)