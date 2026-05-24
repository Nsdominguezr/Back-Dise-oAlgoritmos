from flask import Flask
from config import Config
from models.orders_model import db
from controllers.orders_controller import orders_bp

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
app.register_blueprint(orders_bp)

if __name__ == '__main__':
    # Microservicio corre en el puerto 5004
    app.run(host='0.0.0.0', port=5004, debug=True)