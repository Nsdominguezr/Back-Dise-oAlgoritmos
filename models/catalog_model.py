"""Módulo de modelos de la base de datos del catálogo."""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Sede(db.Model):
    """Modelo de Sede.

    Attributes:
        id: Identificador único de la sede.
        nombre: Nombre de la sede.
        direccion: Dirección de la sede.
        telefono: Teléfono de contacto.
        activo: Bandera de soft delete (True = activo).
    """
    __tablename__ = 'sedes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(150))
    telefono = db.Column(db.String(20))
    activo = db.Column(db.Boolean, default=True)  # <-- NUEVO CAMPO.


class Producto(db.Model):
    """Modelo de Producto.

    Attributes:
        id: Identificador único del producto.
        nombre: Nombre del producto.
        precio: Precio unitario.
        categoria: Categoría del producto.
        activo: Bandera de soft delete (True = activo).
    """
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    categoria = db.Column(db.String(50))
    activo = db.Column(db.Boolean, default=True)