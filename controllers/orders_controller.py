"""
Módulo de controlador de pedidos.
Gestiona las operaciones de pedidos, mesas, caja y pagos.
"""

from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app, make_response
from models.orders_model import db, Mesa, Pedido, DetallePedido, Pago
import requests
from decimal import Decimal
from utils.auth_middleware import (
    admin_local_or_global_required,
    token_required,
    admin_global_required
)
import io
import csv

orders_bp = Blueprint('orders_bp', __name__, url_prefix='/api/pedidos')


# ====================================================================
# ALGORITMO DE LA MOCHILA - OPTIMIZACIÓN DE COLA DE PEDIDOS
# ====================================================================
def leer_entero(valor):
    """Valida que la entrada sea un número entero positivo.

    Args:
        valor: Valor a validar.

    Returns:
        Entero positivo o None si no es válido.
    """
    try:
        v = int(valor)
        return v if v > 0 else None
    except Exception:
        return None

def resolver_mochila_pedidos(pedidos, capacidad):
    """Algoritmo de la Mochila (Programación Dinámica).

    Selecciona la combinación óptima de pedidos que maximiza el
    beneficio total respeando la capacidad máxima de items.

    Args:
        pedidos: Lista de dicts con {id, cantidad_items, total}.
        capacidad: Capacidad máxima de items a procesar.

    Returns:
        Dict con pedidos_seleccionados, items_total y beneficio_total.
    """
    n = len(pedidos)
    if n == 0 or capacidad <= 0:
        return {
            "pedidos_seleccionados": [],
            "items_total": 0,
            "beneficio_total": 0
        }

    # Preparar datos ordenados por beneficio (ratio beneficio/volumen).
    articulos = []
    for p in pedidos:
        ratio = p['total'] / p['cantidad_items'] if p['cantidad_items'] > 0 else 0
        articulos.append({
            "id": p['id'],
            "nombre": p.get('nombre', f"Pedido #{p['id']}"),
            "volumen": p['cantidad_items'],
            "beneficio": p['total'],
            "ratio": ratio
        })

    # Ordenar por ratio beneficio/volumen (más eficiente primero).
    articulos.sort(key=lambda x: x['ratio'], reverse=True)

    # Capacidad máxima = la mayor cantidad de items en un solo pedido.
    capacidad_maxima = max(a['volumen'] for a in articulos) if articulos else capacidad
    # Pero no puede exceder la capacidad real de procesamiento.
    capacidad_maxima = min(capacidad_maxima, capacidad)

    # Inicializar tabla de programación dinámica.
    dp = [[0 for _ in range(capacidad_maxima + 1)] for _ in range(n + 1)]
    combinaciones = [["" for _ in range(capacidad_maxima + 1)] for _ in range(n + 1)]

    # Programación Dinámica: construir tabla de soluciones.
    for i in range(1, n + 1):
        art = articulos[i - 1]
        v_actual = art['volumen']
        b_actual = art['beneficio']

        for j in range(capacidad_maxima + 1):
            beneficio_sin = dp[i - 1][j]
            comb_sin = combinaciones[i - 1][j]

            if v_actual <= j:
                beneficio_con = b_actual + dp[i - 1][j - v_actual]

                if beneficio_con >= beneficio_sin:
                    dp[i][j] = beneficio_con
                    previo = combinaciones[i - 1][j - v_actual]
                    combinaciones[i][j] = f"{previo}+{art['id']}" if previo else str(art['id'])
                else:
                    dp[i][j] = beneficio_sin
                    combinaciones[i][j] = comb_sin
            else:
                dp[i][j] = beneficio_sin
                combinaciones[i][j] = comb_sin

    # Extraer resultado final de la tabla DP.
    resultado_beneficio = dp[n][capacidad_maxima]
    combinacion_str = combinaciones[n][capacidad_maxima]

    # Parsear IDs de pedidos seleccionados.
    pedidos_seleccionados = []
    if combinacion_str:
        pedidos_seleccionados = [int(x) for x in combinacion_str.split('+')]

    # Calcular items totales usados.
    items_total = sum(a['volumen'] for a in articulos if a['id'] in pedidos_seleccionados)

    return {
        "pedidos_seleccionados": pedidos_seleccionados,
        "items_total": items_total,
        "beneficio_total": resultado_beneficio
    }

# ----------------- FUNCIONES DEL MESERO (SPRINT 5) -----------------

# HU-019 / HU-033: Obtener mesas ACTIVAS de una sede (Filtrado para ocultar eliminadas)


@orders_bp.route('/mesas/<int:sede_id>', methods=['GET'])
@token_required
def get_mesas(sede_id):
    """Obtiene las mesas activas de una sede.

    Args:
        sede_id: ID de la sede a consultar.

    Returns:
        Lista de diccionarios con id, numero_mesa y estado.
    """
    # Trae solo las mesas que no han sido dadas de baja lógicamente.
    mesas = Mesa.query.filter_by(sede_id=sede_id, activo=True).all()
    resultado = [
        {"id": m.id, "numero_mesa": m.numero_mesa, "estado": m.estado}
        for m in mesas
    ]
    return jsonify(resultado), 200


@orders_bp.route('/abrir', methods=['POST'])
@token_required
def abrir_pedido():
    """Abre un nuevo pedido para una mesa.

    Args:
        None (datos en JSON: mesa_id, usuario_id).

    Returns:
        Mensaje de éxito con pedido_id o error entsprechend.
    """
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
    """Agrega un item a un pedido abierto.

    Valida stock con el servicio de inventario antes de agregar.

    Args:
        pedido_id: ID del pedido.

    Returns:
        Mensaje con nuevo_total o error entsprechend.
    """
    data = request.get_json()
    pedido = Pedido.query.get(pedido_id)

    if pedido.estado != 'ABIERTO':
        return jsonify({'mensaje': 'El pedido ya no se puede modificar, está en caja o pagado'}), 403

    # Comunicación HTTP con Inventario (Puerto 5003) para validar stock.
    try:
        url = f"{current_app.config['INVENTORY_SERVICE_URL']}/sede/{data['sede_id']}"
        headers = {'Authorization': request.headers.get('Authorization')}
        stock_data = requests.get(url, headers=headers).json()

        stock_disponible = next(
            (item['cantidad'] for item in stock_data if item['producto_id'] == data['producto_id']),
            0
        )
        if stock_disponible < int(data['cantidad']):
            return jsonify(
                {'mensaje': f'Stock insuficiente. Solo hay {stock_disponible} disponibles.'}
            ), 400
    except Exception:
        return jsonify({'mensaje': 'Error comunicándose con el servicio de inventario'}), 503

    nuevo_detalle = DetallePedido(
        pedido_id=pedido.id,
        producto_id=data['producto_id'],
        cantidad=data['cantidad'],
        precio_unitario=data['precio_unitario']
    )
    pedido.total += (int(data['cantidad']) * Decimal(str(data['precio_unitario'])))
    pedido.ultima_actividad = datetime.utcnow()
    db.session.add(nuevo_detalle)
    db.session.commit()
    return jsonify({'mensaje': 'Producto agregado', 'nuevo_total': float(pedido.total)}), 200


# ----------------- FUNCIONES DE LA CAJA (SPRINT 6) -----------------


@orders_bp.route('/<int:pedido_id>/pasar-a-caja', methods=['PATCH'])
@token_required
def pasar_a_caja(pedido_id):
    """Envía un pedido abierto a la caja para su cobro.

    Args:
        pedido_id: ID del pedido.

    Returns:
        Mensaje de éxito o error entsprechend.
    """
    pedido = Pedido.query.get(pedido_id)
    if pedido.estado != 'ABIERTO':
        return jsonify({'mensaje': 'El pedido no se puede congelar'}), 400

    pedido.estado = 'PENDIENTE_PAGO'
    pedido.ultima_actividad = datetime.utcnow()
    db.session.commit()
    return jsonify({'mensaje': 'Pedido enviado a caja. Edición bloqueada.'}), 200


@orders_bp.route('/<int:pedido_id>/checkout', methods=['POST'])
@token_required
def procesar_checkout(pedido_id):
    """Procesa el pago de un pedido y cierra la cuenta.

    Args:
        pedido_id: ID del pedido.

    Returns:
        Mensaje de éxito o error entsprechend.
    """
    data = request.get_json()
    medio_pago = data.get('medio_pago')

    if not medio_pago or medio_pago not in ['EFECTIVO', 'TC', 'TD']:
        return jsonify(
            {'mensaje': 'Debe especificar un medio de pago válido (EFECTIVO, TC, TD)'}
        ), 400

    pedido = Pedido.query.get(pedido_id)
    if pedido.estado != 'PENDIENTE_PAGO':
        return jsonify({'mensaje': 'El pedido debe estar PENDIENTE_PAGO para cobrarlo'}), 400

    mesa = Mesa.query.get(pedido.mesa_id)

    # ====================================================================
    # HU-031: COMUNICACIÓN CON INVENTARIO PARA REDUCCIÓN DE STOCK
    # ====================================================================
    detalles = DetallePedido.query.filter_by(pedido_id=pedido.id).all()
    items_payload = [
        {"producto_id": d.producto_id, "cantidad": d.cantidad}
        for d in detalles
    ]

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
            return jsonify(
                {'mensaje': 'Servicio de inventario caído. No se puede cobrar el pedido.'}
            ), 503
    # ====================================================================

    nuevo_pago = Pago(
        pedido_id=pedido.id,
        medio_pago=medio_pago,
        monto_pagado=pedido.total
    )
    pedido.estado = 'PAGADO'
    mesa.estado = 'LIBRE'

    db.session.add(nuevo_pago)
    db.session.commit()
    return jsonify(
        {'mensaje': 'Checkout exitoso. Cuenta cerrada, mesa liberada y stock descontado.'}
    ), 200


@orders_bp.route('/caja/pendientes/<int:sede_id>', methods=['GET'])
@token_required
def get_pendientes_caja(sede_id):
    """Obtiene pedidos pendientes de pago en una sede.

    Args:
        sede_id: ID de la sede.

    Returns:
        Lista de pedidos pendientes con detalle.
    """
    pedidos_pendientes = db.session.query(
        Pedido
    ).join(Mesa).filter(
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
    """Obtiene el historial de pagos de una sede.

    Args:
        sede_id: ID de la sede.

    Returns:
        Lista de pagos con información de pedido y mesa.
    """
    resultados_db = db.session.query(
        Pago, Pedido, Mesa
    ).join(Pedido, Pago.pedido_id == Pedido.id).join(Mesa, Pedido.mesa_id == Mesa.id).filter(
        Mesa.sede_id == sede_id
    ).order_by(Pago.fecha_pago.desc()).all()

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
    """Crea una nueva mesa en el mapa de la sede.

    Args:
        None (datos en JSON: sede_id, numero_mesa).

    Returns:
        Mensaje de éxito con mesa_id o error entsprechend.
    """
    data = request.get_json()
    sede_id = data.get('sede_id')
    numero_mesa = data.get('numero_mesa')

    if not sede_id or not numero_mesa:
        return jsonify(
            {'mensaje': 'Faltan datos obligatorios (sede_id, numero_mesa)'}
        ), 400

    nueva_mesa = Mesa(sede_id=sede_id, numero_mesa=numero_mesa)
    db.session.add(nueva_mesa)
    db.session.commit()

    return jsonify(
        {'mensaje': f'Mesa {numero_mesa} creada exitosamente', 'mesa_id': nueva_mesa.id}
    ), 201


@orders_bp.route('/mesas/<int:mesa_id>', methods=['PATCH'])
@admin_local_or_global_required
def eliminar_mesa(mesa_id):
    """Realiza un Soft Delete (baja lógica) de una mesa.

    Args:
        mesa_id: ID de la mesa a eliminar.

    Returns:
        Mensaje de éxito o error entsprechend.
    """
    mesa = Mesa.query.get(mesa_id)

    if not mesa:
        return jsonify({'mensaje': 'Mesa no encontrada'}), 404

    if mesa.estado == 'OCUPADA':
        return jsonify(
            {'mensaje': 'No puedes eliminar una mesa que tiene clientes actualmente'}
        ), 400

    # Cambiamos el estado de activación para ocultarla del front
    # operativos sin romper llaves foráneas.
    mesa.activo = False
    db.session.commit()

    return jsonify({'mensaje': 'Mesa eliminada (oculta del mapa) exitosamente'}), 200


# ====================================================================
# REPORTE CSV: FINANCIERO CONSOLIDADO (Reporte #7 - Con nombres de sede)
# ====================================================================
@orders_bp.route('/reportes/financiero', methods=['GET'])
@admin_global_required
def reporte_financiero_csv():
    """Genera CSV con resumen financiero por sede y fecha incluyendo nombres.

    Returns:
        Archivo CSV con columnas: fecha, sede_id, sede_nombre,
        total_efectivo, total_tc, total_td, total_ventas.
    """
    token = request.headers.get('Authorization')
    headers = {'Authorization': token}

    # 1. Obtener info de sedes desde catalog_service.
    sedes_response = requests.get(
        f"{current_app.config['CATALOG_SERVICE_URL']}/sedes",
        headers=headers
    )
    sedes = {s['id']: s['nombre'] for s in sedes_response.json()} if sedes_response.status_code == 200 else {}

    # 2. Obtener todos los pagos con información de sede.
    pagos_data = db.session.query(
        Pago.fecha_pago,
        Pago.medio_pago,
        Pago.monto_pagado,
        Mesa.sede_id,
        Pedido.total
    ).join(Pedido, Pago.pedido_id == Pedido.id).join(Mesa, Pedido.mesa_id == Mesa.id).filter(
        Pedido.estado == 'PAGADO'
    ).order_by(Pago.fecha_pago.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'fecha', 'sede_id', 'sede_nombre',
        'total_efectivo', 'total_tc', 'total_td', 'total_ventas'
    ])

    current_row = []
    last_date = None
    last_sede = None

    for pago in pagos_data:
        fecha = pago.fecha_pago.strftime('%Y-%m-%d')
        sede_id = pago.sede_id
        sede_nombre = sedes.get(sede_id, 'N/A')

        if last_date != fecha or last_sede != sede_id:
            if current_row:
                writer.writerow(current_row)
            last_date = fecha
            last_sede = sede_id
            current_row = [fecha, sede_id, sede_nombre, 0, 0, 0, 0]

        if pago.medio_pago == 'EFECTIVO':
            current_row[3] += float(pago.monto_pagado)
        elif pago.medio_pago == 'TC':
            current_row[4] += float(pago.monto_pagado)
        elif pago.medio_pago == 'TD':
            current_row[5] += float(pago.monto_pagado)

        current_row[6] += float(pago.monto_pagado)

    if current_row:
        writer.writerow(current_row)

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=reporte_financiero.csv'

    return response


# ====================================================================
# ENDPOINT: OPTIMIZACIÓN DE COLA DE PEDIDOS (Mochila DP)
# ====================================================================
@orders_bp.route('/optimizar-cola', methods=['POST'])
@admin_local_or_global_required
def optimizar_cola_pedidos():
    """Optimiza la cola de pedidos usando el algoritmo de la mochila.

    Recibe una sede y capacidad máxima de items.
    Retorna qué pedidos procesar primero para maximizar revenue.

    Args:
        None (datos en JSON: sede_id, capacidad_items).

    Returns:
        Dict con pedidos_seleccionados, items_total, beneficio_total,
        pedidos_omitidos y total_pedidos_pendientes.
    """
    data = request.get_json()
    sede_id = data.get('sede_id')
    capacidad = leer_entero(data.get('capacidad_items', 20))

    if not sede_id:
        return jsonify({'mensaje': 'Se requiere sede_id'}), 400
    if not capacidad:
        return jsonify({'mensaje': 'Capacidad debe ser un número entero positivo'}), 400

    # Obtener pedidos pendientes de pago en esta sede.
    pedidos_pendientes = db.session.query(
        Pedido.id,
        Pedido.total,
        Pedido.fecha_creacion
    ).join(Mesa, Pedido.mesa_id == Mesa.id).filter(
        Mesa.sede_id == sede_id,
        Pedido.estado == 'PENDIENTE_PAGO'
    ).order_by(Pedido.fecha_creacion.asc()).all()

    if not pedidos_pendientes:
        return jsonify({
            'mensaje': 'No hay pedidos pendientes en esta sede',
            'pedidos_seleccionados': [],
            'items_total': 0,
            'beneficio_total': 0
        }), 200

    # Calcular cantidad de items por pedido desde DetallePedido.
    pedidos_data = []
    for p in pedidos_pendientes:
        detalles = DetallePedido.query.filter_by(pedido_id=p.id).all()
        cantidad_items = sum(d.cantidad for d in detalles)

        pedidos_data.append({
            'id': p.id,
            'cantidad_items': cantidad_items if cantidad_items > 0 else 1,
            'total': float(p.total) if p.total else 0
        })

    # Ejecutar algoritmo de la mochila.
    resultado = resolver_mochila_pedidos(pedidos_data, capacidad)

    # Obtener IDs de pedidos no seleccionados.
    todos_los_ids = [p['id'] for p in pedidos_data]
    pedidos_omitidos = [
        pid for pid in todos_los_ids
        if pid not in resultado['pedidos_seleccionados']
    ]

    return jsonify({
        'sede_id': sede_id,
        'capacidad_items': capacidad,
        'pedidos_seleccionados': resultado['pedidos_seleccionados'],
        'items_total': resultado['items_total'],
        'beneficio_total': resultado['beneficio_total'],
        'pedidos_omitidos': pedidos_omitidos,
        'total_pedidos_pendientes': len(pedidos_data)
    }), 200


# ====================================================================
# JOB: LIBERAR MESAS ABANDONADAS
# ====================================================================
@orders_bp.route('/limpiar-mesas-abandonadas', methods=['POST'])
@admin_local_or_global_required
def limpiar_mesas_abandonadas():
    """Libera mesas con pedidos en estado ABIERTO sin actividad reciente.

    Args:
        minutos_inactividad: Minutos sin actividad para considerar abandonado.

    Returns:
        Mensaje con cantidad de mesas liberadas.
    """
    data = request.get_json()
    minutos_inactividad = data.get('minutos_inactividad', 30)

    if not isinstance(minutos_inactividad, int) or minutos_inactividad <= 0:
        return jsonify({'mensaje': 'minutos_inactividad debe ser un entero positivo'}), 400

    limite = datetime.utcnow() - timedelta(minutes=minutos_inactividad)

    pedidos_abandonados = Pedido.query.filter(
        Pedido.estado == 'ABIERTO',
        Pedido.ultima_actividad < limite
    ).all()

    count = 0
    for pedido in pedidos_abandonados:
        mesa = Mesa.query.get(pedido.mesa_id)
        if mesa and mesa.estado == 'OCUPADA':
            mesa.estado = 'LIBRE'
        pedido.estado = 'CANCELADO'
        db.session.commit()
        count += 1

    return jsonify({
        'mensaje': f'Se liberaron {count} mesas abandonadas',
        'mesas_liberadas': count
    }), 200