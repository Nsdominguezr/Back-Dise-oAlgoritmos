import os

class Config:
    SECRET_KEY = 'super-secret-key-para-jwt'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:12345@localhost/bar_orders_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Aquí es donde el Sprint 5 se conecta con el Sprint 4 (Inventario)
    INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://127.0.0.1:5003/api/inventario")