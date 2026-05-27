from flask import Blueprint, request, jsonify, current_app
from models.orders_model import db, Mesa, Pedido, DetallePedido, Pago
import requests
from decimal import Decimal
from utils.auth_middleware import admin_local_or_global_required, token_required

orders_bp = Blueprint('orders_bp', __name__, url_prefix='/api/pedidos')

# ----------------- FUNCIONES DEL MESERO (SPRINT 5) -----------------

# HU-019 / HU-033: Obtener mesas ACTIVAS de una sede (Filtrado para ocultar eliminadas)
@orders_bp.route('/mesas/<int:sede_id>', methods=['GET'])
@token_required
def get_mesas(sede_id):
    # Trae solo las mesas que no han sido dadas de baja lógicamente
    mesas = Mesa.query.filter_by(sede_id=sede_id, activo=True).all()
    resultado = [{"id": m.id, "numero_mesa": m.numero_mesa, "estado": m.estado} for m in mesas]
    return jsonify(resultado), 200

@orders_bp.route('/abrir', methods=['POST'])
@token_required
def abrir_pedido():
    data = request.get_json()
    mesa = Mesa.query.get(data['mesa_id'])
    
    if not mesa or not mesa.activo:
        return jsonify({'mensaje': 'Mesa no disponible o inexistente'}), 404
        
    if mesa.estado == 'OCUPADA':
        return jsonify({'mensaje': 'La mesa ya está ocupada'}), 400
        
    mesa.estado = 'OCUPADA'
    nuevo_pedido = Pedido(mesa_id=mesa.id, usuario_id=data['usuario_id'])
    db.session.add(nuevo_pedido)
    db.session.commit()
    return jsonify({'mensaje': 'Pedido abierto', 'pedido_id': nuevo_pedido.id}), 201

@orders_bp.route('/<int:pedido_id>/items', methods=['POST'])
@token_required
def agregar_item(pedido_id):
    data = request.get_json()
    pedido = Pedido.query.get(pedido_id)
    
    if pedido.estado != 'ABIERTO':
        return jsonify({'mensaje': 'El pedido ya no se puede modificar, está en caja o pagado'}), 403

    # Comunicación HTTP con Inventario (Puerto 5003) para validar stock
    try:
        url = f"{current_app.config['INVENTORY_SERVICE_URL']}/sede/{data['sede_id']}"
        headers = {'Authorization': request.headers.get('Authorization')}
        stock_data = requests.get(url, headers=headers).json()
        
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
@token_required
def pasar_a_caja(pedido_id):
    pedido = Pedido.query.get(pedido_id)
    if pedido.estado != 'ABIERTO':
        return jsonify({'mensaje': 'El pedido no se puede congelar'}), 400

    pedido.estado = 'PENDIENTE_PAGO'
    db.session.commit()
    return jsonify({'mensaje': 'Pedido enviado a caja. Edición bloqueada.'}), 200

@orders_bp.route('/<int:pedido_id>/checkout', methods=['POST'])
@token_required
def procesar_checkout(pedido_id):
    data = request.get_json()
    medio_pago = data.get('medio_pago')
    
    if not medio_pago or medio_pago not in ['EFECTIVO', 'TC', 'TD']:
        return jsonify({'mensaje': 'Debe especificar un medio de pago válido (EFECTIVO, TC, TD)'}), 400

    pedido = Pedido.query.get(pedido_id)
    if pedido.estado != 'PENDIENTE_PAGO':
        return jsonify({'mensaje': 'El pedido debe estar PENDIENTE_PAGO para cobrarlo'}), 400

    mesa = Mesa.query.get(pedido.mesa_id)
    
    # ====================================================================
    # HU-031: COMUNICACIÓN CON INVENTARIO PARA REDUCCIÓN DE STOCK
    # ====================================================================
    detalles = DetallePedido.query.filter_by(pedido_id=pedido.id).all()
    items_payload = [{"producto_id": d.producto_id, "cantidad": d.cantidad} for d in detalles]
    
    if items_payload:
        try:
            inventario_url = f"{current_app.config['INVENTORY_SERVICE_URL']}/descontar-venta"
            payload = {
                "sede_id": mesa.sede_id,
                "usuario_id": pedido.usuario_id,
                "items": items_payload
            }
            headers = {'Authorization': request.headers.get('Authorization')}
            respuesta = requests.post(inventario_url, json=payload, headers=headers)
            
            if respuesta.status_code != 200:
                return jsonify({
                    'mensaje': 'Transacción rechazada. Error al descontar stock en bodega.', 
                    'detalle': respuesta.json()
                }), 400
                
        except requests.exceptions.RequestException:
            return jsonify({'mensaje': 'Servicio de inventario caído. No se puede cobrar el pedido.'}), 503
    # ====================================================================

    nuevo_pago = Pago(pedido_id=pedido.id, medio_pago=medio_pago, monto_pagado=pedido.total)
    pedido.estado = 'PAGADO'
    mesa.estado = 'LIBRE'

    db.session.add(nuevo_pago)
    db.session.commit()
    return jsonify({'mensaje': 'Checkout exitoso. Cuenta cerrada, mesa liberada y stock descontado.'}), 200

@orders_bp.route('/caja/pendientes/<int:sede_id>', methods=['GET'])
@token_required
def get_pendientes_caja(sede_id):
    pedidos_pendientes = Pedido.query.join(Mesa).filter(
        Mesa.sede_id == sede_id,
        Pedido.estado == 'PENDIENTE_PAGO'
    ).all()
    
    resultado = []
    for p in pedidos_pendientes:
        resultado.append({
            "pedido_id": p.id,
            "numero_mesa": p.mesa_ref.numero_mesa,
            "total": float(p.total),
            "fecha": p.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify(resultado), 200


# ====================================================================
# HU-032: HISTORIAL Y TRAZABILIDAD DE PAGOS (VISTA ADMIN)
# ====================================================================
@orders_bp.route('/pagos/historial/<int:sede_id>', methods=['GET'])
@token_required
def historial_pagos(sede_id):
    resultados_db = db.session.query(Pago, Pedido, Mesa)\
        .join(Pedido, Pago.pedido_id == Pedido.id)\
        .join(Mesa, Pedido.mesa_id == Mesa.id)\
        .filter(Mesa.sede_id == sede_id)\
        .order_by(Pago.fecha_pago.desc())\
        .all()
    
    historial = []
    for pago, pedido, mesa in resultados_db:
        historial.append({
            "pago_id": pago.id,
            "pedido_id": pedido.id,
            "numero_mesa": mesa.numero_mesa,
            "usuario_cajero_id": pedido.usuario_id,
            "medio_pago": pago.medio_pago,
            "monto_cobrado": float(pago.monto_pagado),
            "fecha_pago": pago.fecha_pago.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    return jsonify(historial), 200


# ====================================================================
# HU-033: GESTIÓN DE MESAS (CREACIÓN Y ELIMINACIÓN)
# ====================================================================
@orders_bp.route('/mesas', methods=['POST'])
@admin_local_or_global_required
def crear_mesa():
    """Crea una nueva mesa en el mapa de la sede"""
    data = request.get_json()
    sede_id = data.get('sede_id')
    numero_mesa = data.get('numero_mesa')

    if not sede_id or not numero_mesa:
        return jsonify({'mensaje': 'Faltan datos obligatorios (sede_id, numero_mesa)'}), 400

    nueva_mesa = Mesa(sede_id=sede_id, numero_mesa=numero_mesa)
    db.session.add(nueva_mesa)
    db.session.commit()

    return jsonify({'mensaje': f'Mesa {numero_mesa} creada exitosamente', 'mesa_id': nueva_mesa.id}), 201


@orders_bp.route('/mesas/<int:mesa_id>', methods=['PATCH'])
@admin_local_or_global_required
def eliminar_mesa(mesa_id):
    """Realiza un Soft Delete (baja lógica) de una mesa"""
    mesa = Mesa.query.get(mesa_id)
    
    if not mesa:
        return jsonify({'mensaje': 'Mesa no encontrada'}), 404
        
    if mesa.estado == 'OCUPADA':
        return jsonify({'mensaje': 'No puedes eliminar una mesa que tiene clientes actualmente'}), 400

    # Cambiamos el estado de activación para ocultarla del front operativos sin romper llaves foráneas
    mesa.activo = False
    db.session.commit()
    
    return jsonify({'mensaje': 'Mesa eliminada (oculta del mapa) exitosamente'}), 200