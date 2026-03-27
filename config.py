import os

class Config:
    # Configuración hacia la base de datos específica de Identidad
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql+pymysql://root:12345@localhost/bar_identity_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'super-secret-key-para-jwt'