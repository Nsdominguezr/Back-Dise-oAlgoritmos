"""Módulo de configuración del servicio de inventario."""


class Config:
    """Configuración del servicio de inventario.

    Attributes:
        SECRET_KEY: Clave secreta para JWT.
        SQLALCHEMY_DATABASE_URI: URI de la base de datos MySQL.
        SQLALCHEMY_TRACK_MODIFICATIONS: Desactiva tracking de modificaciones.
        CATALOG_SERVICE_URL: URL del servicio de catálogo.
    """
    SECRET_KEY = 'super-secret-key-para-jwt'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:12345@localhost/bar_inventory_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CATALOG_SERVICE_URL = 'http://127.0.0.1:5002/api'