from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Mesa(db.Model):
    __tablename__ = 'mesas'
    id = db.Column(db.Integer, primary_key=True)
    sede_id = db.Column(db.Integer, nullable=False)
    numero_mesa = db.Column(db.String(10), nullable=False)
    estado = db.Column(db.Enum('LIBRE', 'OCUPADA'), default='LIBRE')
    activo = db.Column(db.Boolean, default=True) # <-- NUEVO CAMPO PARA SOFT DELETE

class Pedido(db.Model):
    __tablename__ = 'pedidos'
    id = db.Column(db.Integer, primary_key=True)
    mesa_id = db.Column(db.Integer, db.ForeignKey('mesas.id'), nullable=False)
    usuario_id = db.Column(db.Integer, nullable=False)
    estado = db.Column(db.Enum('ABIERTO', 'PENDIENTE_PAGO', 'PAGADO'), default='ABIERTO')
    total = db.Column(db.Numeric(10, 2), default=0.00)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    mesa_ref = db.relationship('Mesa', backref='pedidos', lazy=True)

class DetallePedido(db.Model):
    __tablename__ = 'detalles_pedido'
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    producto_id = db.Column(db.Integer, nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)

class Pago(db.Model):
    __tablename__ = 'pagos'
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    medio_pago = db.Column(db.Enum('EFECTIVO', 'TC', 'TD'), nullable=False)
    monto_pagado = db.Column(db.Numeric(10, 2), nullable=False)
    fecha_pago = db.Column(db.DateTime, default=datetime.utcnow)