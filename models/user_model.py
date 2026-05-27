"""Módulo de modelos de la base de datos de identidad."""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Rol(db.Model):
    """Modelo de Rol de usuario.

    Attributes:
        id: Identificador único del rol.
        nombre: Nombre del rol (ej: 'Admin Global', 'Admin Local', 'Mesero').
    """
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)


class Usuario(db.Model):
    """Modelo de Usuario.

    Attributes:
        id: Identificador único del usuario.
        username: Nombre de usuario único.
        password_hash: Hash de la contraseña encriptada.
        rol_id: ID del rol asignado al usuario.
        sede_id: ID de la sede donde trabaja el usuario.
        creado_en: Fecha de creación de la cuenta.
        activo: Bandera de soft delete (True = activo).
        rol: Relación con el modelo Rol.
    """
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    sede_id = db.Column(db.Integer, nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)  # <-- NUEVO CAMPO (HU-035).

    # Relación con el rol.
    rol = db.relationship('Rol', backref='usuarios')