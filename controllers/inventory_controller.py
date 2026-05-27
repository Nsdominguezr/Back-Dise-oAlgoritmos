from flask import Blueprint, request, jsonify, make_response
from models.inventory_model import db, Inventario, MovimientoInventario
from dto.inventory_dto import inventario_dto, inventarios_dto
from utils.auth_middleware import admin_global_required, admin_local_or_global_required, token_required
import jwt
import io
import csv
import requests
from flask import current_app

inventory_bp = Blueprint('inventory_bp', __name__, url_prefix='/api/inventario')

# Función auxiliar para extraer el usuario_id del token (para el historial)
def get_user_from_token(req):
    token = req.headers['Authorization'].split(" ")[1]
    data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
    return data['user_id']

@inventory_bp.route('/sede/<int:sede_id>', methods=['GET'])
@token_required
def get_stock_sede(sede_id):
    """Vista de stock por sede"""
    stock = Inventario.query.filter_by(sede_id=sede_id).all()
    return jsonify(inventarios_dto.dump(stock)), 200

@inventory_bp.route('/movimiento', methods=['POST'])
@admin_local_or_global_required
def registrar_movimiento():
    """Registra ingreso o merma manual y actualiza el stock exacto"""
    data = request.get_json()
    sede_id = data.get('sede_id')
    producto_id = data.get('producto_id')
    tipo_movimiento = data.get('tipo_movimiento') # 'INGRESO' o 'MERMA'
    cantidad_mov = int(data.get('cantidad', 0)) # Validación a entero
    
    if cantidad_mov <= 0:
        return jsonify({'mensaje': 'La cantidad debe ser un entero positivo'}), 400
        
    usuario_id = get_user_from_token(request)

    # 1. Buscar si ya existe la fila de stock para este producto en esta sede
    registro_stock = Inventario.query.filter_by(sede_id=sede_id, producto_id=producto_id).first()
    
    if not registro_stock:
        # Si no existe, se crea en 0
        registro_stock = Inventario(sede_id=sede_id, producto_id=producto_id, cantidad=0)
        db.session.add(registro_stock)
        db.session.flush() # Obtiene el ID temporal para usarlo en el movimiento

    # 2. Calcular nueva cantidad
    if tipo_movimiento == 'INGRESO':
        registro_stock.cantidad += cantidad_mov
    elif tipo_movimiento == 'MERMA':
        if registro_stock.cantidad < cantidad_mov:
            return jsonify({'mensaje': 'Stock insuficiente para aplicar esta merma'}), 400
        registro_stock.cantidad -= cantidad_mov
    else:
        return jsonify({'mensaje': 'Tipo de movimiento inválido'}), 400

    # 3. Registrar el historial
    nuevo_movimiento = MovimientoInventario(
        inventario_id=registro_stock.id,
        usuario_id=usuario_id,
        tipo_movimiento=tipo_movimiento,
        cantidad=cantidad_mov,
        observacion=data.get('observacion', '')
    )
    
    try:
        db.session.add(nuevo_movimiento)
        db.session.commit()
        return jsonify(inventario_dto.dump(registro_stock)), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'mensaje': 'Error en la transacción de inventario'}), 500
    
@inventory_bp.route('/descontar-venta', methods=['POST'])
@token_required
def descontar_venta():
    """Endpoint interno: Descuenta el stock automáticamente al pagar una cuenta"""
    data = request.get_json()
    sede_id = data.get('sede_id')
    usuario_id = data.get('usuario_id') # El cajero que cerró la cuenta
    items = data.get('items') # Lista de diccionarios: [{'producto_id': 1, 'cantidad': 2}, ...]
    
    if not items or not sede_id:
        return jsonify({'mensaje': 'Datos de venta incompletos'}), 400

    try:
        for item in items:
            producto_id = item['producto_id']
            cantidad_vendida = int(item['cantidad'])
            
            registro_stock = Inventario.query.filter_by(sede_id=sede_id, producto_id=producto_id).first()
            
            # Si el producto no existe o el stock bajó desde que se tomó el pedido
            if not registro_stock or registro_stock.cantidad < cantidad_vendida:
                return jsonify({'mensaje': f'Stock inconsistente para el producto {producto_id}. Venta detenida.'}), 400
                
            # 1. Descontar stock
            registro_stock.cantidad -= cantidad_vendida
            
            # 2. Guardar historial de auditoría
            nuevo_movimiento = MovimientoInventario(
                inventario_id=registro_stock.id,
                usuario_id=usuario_id,
                tipo_movimiento='VENTA',
                cantidad=cantidad_vendida,
                observacion='Venta procesada en caja'
            )
            db.session.add(nuevo_movimiento)
            
        db.session.commit()
        return jsonify({'mensaje': 'Stock descontado con éxito'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'mensaje': 'Error procesando el descuento de inventario'}), 500


# ====================================================================
# REPORTE CSV: INVENTARIO POR SEDE (Con nombres)
# ====================================================================
@inventory_bp.route('/reportes/inventario', methods=['GET'])
@admin_global_required
def reporte_inventario_csv():
    """Genera CSV con stock actual por sede incluyendo nombres de productos y sedes"""
    token = request.headers.get('Authorization')
    headers = {'Authorization': token}

    # 1. Obtener todos los inventarios
    inventarios = Inventario.query.all()

    # 2. Obtener info de productos desde catalog_service
    productos_response = requests.get(
        f"{current_app.config['CATALOG_SERVICE_URL']}/productos",
        headers=headers
    )
    productos = {p['id']: p for p in productos_response.json()} if productos_response.status_code == 200 else {}

    # 3. Obtener info de sedes desde catalog_service
    sedes_response = requests.get(
        f"{current_app.config['CATALOG_SERVICE_URL']}/sedes",
        headers=headers
    )
    sedes = {s['id']: s for s in sedes_response.json()} if sedes_response.status_code == 200 else {}

    # Crear CSV en memoria
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['sede_id', 'sede_nombre', 'producto_id', 'producto_nombre', 'stock_actual', 'precio_unitario'])

    for inv in inventarios:
        producto = productos.get(inv.producto_id, {})
        sede = sedes.get(inv.sede_id, {})

        writer.writerow([
            inv.sede_id,
            sede.get('nombre', 'N/A'),
            inv.producto_id,
            producto.get('nombre', 'N/A'),
            inv.cantidad,
            producto.get('precio', 'N/A')
        ])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=reporte_inventario.csv'

    return response