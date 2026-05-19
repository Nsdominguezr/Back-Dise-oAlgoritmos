from flask import Flask
from config import Config
from models.inventory_model import db
from dto.inventory_dto import ma
from controllers.inventory_controller import inventory_bp

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
ma.init_app(app)

app.register_blueprint(inventory_bp)

if __name__ == '__main__':
    # Microservicio de inventario en puerto aislado
    app.run(host='0.0.0.0', port=5003, debug=True)