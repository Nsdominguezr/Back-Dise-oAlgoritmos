from flask import Flask
from config import Config
from models.user_model import db
from dto.user_dto import ma
from controllers.auth_controller import auth_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar extensiones
    db.init_app(app)
    ma.init_app(app)

    # Registrar Blueprints (Controladores)
    app.register_blueprint(auth_bp)

    return app

app = create_app()

if __name__ == '__main__':
    # Creación de tablas si no existen (útil para entorno de desarrollo)
    with app.app_context():
        db.create_all()
        
    app.run(host='0.0.0.0', port=5001, debug=True)