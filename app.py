"""Aplicación Flask del servicio de catálogo.

Punto de entrada para el microservicio de catálogo.
"""

from flask import Flask
from config import Config
from models.catalog_model import db
from dto.catalog_dto import ma
from controllers.sedes_controller import sedes_bp
from controllers.productos_controller import productos_bp

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
ma.init_app(app)

# Registrar rutas.
app.register_blueprint(sedes_bp)
app.register_blueprint(productos_bp)

if __name__ == '__main__':
    # Este microservicio corre en el puerto 5002.
    app.run(host='0.0.0.0', port=5002, debug=True)