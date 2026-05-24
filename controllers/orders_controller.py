from flask import Blueprint, request, jsonify, current_app
from models.orders_model import db, Mesa, Pedido, DetallePedido, Pago
import requests
from decimal import Decimal

orders_bp = Blueprint('orders_bp', __name__, url_prefix='/api/pedidos')

# ----------------- FUNCIONES DEL MESERO (SPRINT 5) -----------------

@orders_bp.route('/abrir', methods=['POST'])
def abrir_pedido():
    data = request.get_json()
    mesa = Mesa.query.get(data['mesa_id'])
    
    if mesa.estado == 'OCUPADA':
        return jsonify({'mensaje': 'La mesa ya está ocupada'}), 400
        
    mesa.estado = 'OCUPADA'
    nuevo_pedido = Pedido(mesa_id=mesa.id, usuario_id=data['usuario_id'])
    db.session.add(nuevo_pedido)
    db.session.commit()
    return jsonify({'mensaje': 'Pedido abierto', 'pedido_id': nuevo_pedido.id}), 201

@orders_bp.route('/<int:pedido_id>/items', methods=['POST'])
def agregar_item(pedido_id):
    data = request.get_json()
    pedido = Pedido.query.get(pedido_id)
    
    if pedido.estado != 'ABIERTO':
        return jsonify({'mensaje': 'El pedido ya no se puede modificar, está en caja o pagado'}), 403

    # Comunicación HTTP con Inventario (Puerto 5003) para validar stock
    try:
        url = f"{current_app.config['INVENTORY_SERVICE_URL']}/sede/{data['sede_id']}"
        stock_data = requests.get(url).json()
        
        stock_disponible = next((item['cantidad'] for item in stock_data if item['producto_id'] == data['producto_id']), 0)
        if stock_disponible < int(data['cantidad']):
            return jsonify({'mensaje': f'Stock insuficiente. Solo hay {stock_disponible} disponibles.'}), 400
    except Exception:
        return jsonify({'mensaje': 'Error comunicándose con el servicio de inventario'}), 503

    nuevo_detalle = DetallePedido(
        pedido_id=pedido.id, 
        producto_id=data['producto_id'], 
        cantidad=data['cantidad'], 
        precio_unitario=data['precio_unitario']
    )
    pedido.total += (int(data['cantidad']) * Decimal(str(data['precio_unitario'])))
    db.session.add(nuevo_detalle)
    db.session.commit()
    return jsonify({'mensaje': 'Producto agregado', 'nuevo_total': float(pedido.total)}), 200


# ----------------- FUNCIONES DE LA CAJA (SPRINT 6) -----------------

@orders_bp.route('/<int:pedido_id>/pasar-a-caja', methods=['PATCH'])
def pasar_a_caja(pedido_id):
    pedido = Pedido.query.get(pedido_id)
    if pedido.estado != 'ABIERTO':
        return jsonify({'mensaje': 'El pedido no se puede congelar'}), 400

    pedido.estado = 'PENDIENTE_PAGO'
    db.session.commit()
    return jsonify({'mensaje': 'Pedido enviado a caja. Edición bloqueada.'}), 200

@orders_bp.route('/<int:pedido_id>/checkout', methods=['POST'])
def procesar_checkout(pedido_id):
    data = request.get_json()
    medio_pago = data.get('medio_pago')
    
    if not medio_pago or medio_pago not in ['EFECTIVO', 'TC', 'TD']:
        return jsonify({'mensaje': 'Debe especificar un medio de pago válido (EFECTIVO, TC, TD)'}), 400

    pedido = Pedido.query.get(pedido_id)
    if pedido.estado != 'PENDIENTE_PAGO':
        return jsonify({'mensaje': 'El pedido debe estar PENDIENTE_PAGO para cobrarlo'}), 400

    nuevo_pago = Pago(pedido_id=pedido.id, medio_pago=medio_pago, monto_pagado=pedido.total)
    pedido.estado = 'PAGADO'
    
    mesa = Mesa.query.get(pedido.mesa_id)
    mesa.estado = 'LIBRE' # Se libera la mesa

    db.session.add(nuevo_pago)
    db.session.commit()
    return jsonify({'mensaje': 'Checkout exitoso. Cuenta cerrada y mesa liberada.'}), 200

# HU-025 (Vista Cajero): Obtener todas las cuentas pendientes por sede
@orders_bp.route('/caja/pendientes/<int:sede_id>', methods=['GET'])
def get_pendientes_caja(sede_id):
    # Trae los pedidos en revisión de pago cruzando la información con las mesas de la sede
    pedidos_pendientes = Pedido.query.join(Mesa).filter(
        Mesa.sede_id == sede_id,
        Pedido.estado == 'PENDIENTE_PAGO'
    ).all()
    
    resultado = []
    for p in pedidos_pendientes:
        resultado.append({
            "pedido_id": p.id,
            "numero_mesa": p.mesa_ref.numero_mesa,
            "total": float(p.total), # Usamos float aquí solo para serializarlo en el JSON
            "fecha": p.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify(resultado), 200