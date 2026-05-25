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

    mesa = Mesa.query.get(pedido.mesa_id)
    
    # ====================================================================
    # HU-031: COMUNICACIÓN CON INVENTARIO PARA REDUCCIÓN DE STOCK
    # ====================================================================
    # 1. Recopilamos todos los ítems consumidos en este pedido
    detalles = DetallePedido.query.filter_by(pedido_id=pedido.id).all()
    items_payload = [{"producto_id": d.producto_id, "cantidad": d.cantidad} for d in detalles]
    
    if items_payload:
        try:
            # Construimos la URL hacia el microservicio de Inventario
            inventario_url = f"{current_app.config['INVENTORY_SERVICE_URL']}/descontar-venta"
            
            # Armamos el paquete de datos
            payload = {
                "sede_id": mesa.sede_id,
                "usuario_id": pedido.usuario_id, # O el ID del cajero si lo pasas en el JWT
                "items": items_payload
            }
            
            # Disparamos la petición POST
            respuesta = requests.post(inventario_url, json=payload)
            
            # Si el inventario falla (ej. alguien hizo merma manual y ya no alcanzan), bloqueamos el checkout
            if respuesta.status_code != 200:
                return jsonify({
                    'mensaje': 'Transacción rechazada. Error al descontar stock en bodega.', 
                    'detalle': respuesta.json()
                }), 400
                
        except requests.exceptions.RequestException:
            return jsonify({'mensaje': 'Servicio de inventario caído. No se puede cobrar el pedido.'}), 503
    # ====================================================================

    # Si la comunicación fue exitosa (o si no había ítems), procedemos con el cierre financiero
    nuevo_pago = Pago(pedido_id=pedido.id, medio_pago=medio_pago, monto_pagado=pedido.total)
    pedido.estado = 'PAGADO'
    mesa.estado = 'LIBRE' # Se libera la mesa

    db.session.add(nuevo_pago)
    db.session.commit()
    return jsonify({'mensaje': 'Checkout exitoso. Cuenta cerrada, mesa liberada y stock descontado.'}), 200

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

# ====================================================================
# HU-032: HISTORIAL Y TRAZABILIDAD DE PAGOS (VISTA ADMIN)
# ====================================================================
@orders_bp.route('/pagos/historial/<int:sede_id>', methods=['GET'])
def historial_pagos(sede_id):
    """Devuelve el historial de todas las cuentas pagadas de una sede específica"""
    
    # Hacemos un JOIN de las 3 tablas: Pago -> Pedido -> Mesa
    # Filtramos por sede_id y ordenamos del pago más reciente al más antiguo
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
            "usuario_cajero_id": pedido.usuario_id, # ID de quien cobró/abrió la mesa
            "medio_pago": pago.medio_pago,
            "monto_cobrado": float(pago.monto_pagado), # Casteo a float para el JSON
            "fecha_pago": pago.fecha_pago.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    return jsonify(historial), 200