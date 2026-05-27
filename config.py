"""Módulo de configuración del servicio de catálogo."""

import os


class Config:
    """Configuración del servicio de catálogo.

    Attributes:
        SECRET_KEY: Clave secreta para JWT.
        SQLALCHEMY_DATABASE_URI: URI de la base de datos MySQL.
        SQLALCHEMY_TRACK_MODIFICATIONS: Desactiva tracking de modificaciones.
    """
    # ¡Debe ser la MISMA clave que usa Identity!
    SECRET_KEY = 'super-secret-key-para-jwt'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:12345@localhost/bar_catalog_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False