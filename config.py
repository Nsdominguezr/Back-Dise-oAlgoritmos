import os

class Config:
    # Configuración hacia la base de datos específica de Identidad
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql+pymysql://root:12345@localhost/bar_identity_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'super-secret-key-para-jwt'

    # URLs de microservicios para reportes
    INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://127.0.0.1:5003/api/inventario")
    ORDERS_SERVICE_URL = os.getenv("ORDERS_SERVICE_URL", "http://127.0.0.1:5004/api/pedidos")