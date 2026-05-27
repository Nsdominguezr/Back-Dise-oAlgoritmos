"""Módulo de modelos de la base de datos de inventario."""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Inventario(db.Model):
    """Modelo de Inventario por sede y producto.

    Attributes:
        id: Identificador único del registro.
        sede_id: ID de la sede.
        producto_id: ID del producto.
        cantidad: Stock actual del producto en la sede.
        movimientos: Relación con el historial de movimientos.
    """
    __tablename__ = 'inventario'
    id = db.Column(db.Integer, primary_key=True)
    sede_id = db.Column(db.Integer, nullable=False)
    producto_id = db.Column(db.Integer, nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=0)

    # Relación para extraer el historial fácilmente.
    movimientos = db.relationship(
        'MovimientoInventario',
        backref='inventario_ref',
        lazy=True
    )


class MovimientoInventario(db.Model):
    """Modelo de Movimiento de Inventario (historial).

    Attributes:
        id: Identificador único del movimiento.
        inventario_id: ID del registro de inventario asociado.
        usuario_id: ID del usuario que realizó el movimiento.
        tipo_movimiento: Tipo ('INGRESO', 'MERMA', 'VENTA').
        cantidad: Cantidad involucrada en el movimiento.
        fecha: Fecha y hora del movimiento.
        observacion: Descripción opcional del movimiento.
    """
    __tablename__ = 'movimientos_inventario'
    id = db.Column(db.Integer, primary_key=True)
    inventario_id = db.Column(
        db.Integer,
        db.ForeignKey('inventario.id'),
        nullable=False
    )
    usuario_id = db.Column(db.Integer, nullable=False)
    tipo_movimiento = db.Column(
        db.Enum('INGRESO', 'MERMA', 'VENTA'),
        nullable=False
    )
    cantidad = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    observacion = db.Column(db.String(255))