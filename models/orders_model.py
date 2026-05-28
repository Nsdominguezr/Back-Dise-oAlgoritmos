"""Módulo de modelos de la base de datos de pedidos."""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Mesa(db.Model):
    """Modelo de Mesa.

    Attributes:
        id: Identificador único de la mesa.
        sede_id: ID de la sede donde se encuentra la mesa.
        numero_mesa: Número o identificador de la mesa.
        estado: Estado ('LIBRE' o 'OCUPADA').
        activo: Bandera de soft delete (True = activa).
    """
    __tablename__ = 'mesas'
    id = db.Column(db.Integer, primary_key=True)
    sede_id = db.Column(db.Integer, nullable=False)
    numero_mesa = db.Column(db.String(10), nullable=False)
    estado = db.Column(db.Enum('LIBRE', 'OCUPADA'), default='LIBRE')
    activo = db.Column(db.Boolean, default=True)  # <-- NUEVO CAMPO PARA SOFT DELETE.


class Pedido(db.Model):
    """Modelo de Pedido.

    Attributes:
        id: Identificador único del pedido.
        mesa_id: ID de la mesa asociada al pedido.
        usuario_id: ID del mesero que creó el pedido.
        estado: Estado ('ABIERTO', 'PENDIENTE_PAGO', 'PAGADO').
        total: Monto total del pedido.
        fecha_creacion: Fecha y hora de creación.
        mesa_ref: Relación con la mesa.
    """
    __tablename__ = 'pedidos'
    id = db.Column(db.Integer, primary_key=True)
    mesa_id = db.Column(db.Integer, db.ForeignKey('mesas.id'), nullable=False)
    usuario_id = db.Column(db.Integer, nullable=False)
    estado = db.Column(
        db.Enum('ABIERTO', 'PENDIENTE_PAGO', 'PAGADO'),
        default='ABIERTO'
    )
    total = db.Column(db.Numeric(10, 2), default=0.00)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    ultima_actividad = db.Column(db.DateTime, default=datetime.utcnow)

    mesa_ref = db.relationship('Mesa', backref='pedidos', lazy=True)


class DetallePedido(db.Model):
    """Modelo de Detalle de Pedido (ítems del pedido).

    Attributes:
        id: Identificador único del detalle.
        pedido_id: ID del pedido padre.
        producto_id: ID del producto ordenado.
        cantidad: Cantidad solicitada.
        precio_unitario: Precio por unidad al momento del pedido.
    """
    __tablename__ = 'detalles_pedido'
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    producto_id = db.Column(db.Integer, nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)


class Pago(db.Model):
    """Modelo de Pago.

    Attributes:
        id: Identificador único del pago.
        pedido_id: ID del pedido asociado.
        medio_pago: Medio de pago ('EFECTIVO', 'TC', 'TD').
        monto_pagado: Monto pagado.
        fecha_pago: Fecha y hora del pago.
    """
    __tablename__ = 'pagos'
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    medio_pago = db.Column(db.Enum('EFECTIVO', 'TC', 'TD'), nullable=False)
    monto_pagado = db.Column(db.Numeric(10, 2), nullable=False)
    fecha_pago = db.Column(db.DateTime, default=datetime.utcnow)