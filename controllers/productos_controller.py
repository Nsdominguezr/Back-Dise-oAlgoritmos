from flask import Blueprint, request, jsonify
from models.catalog_model import db, Producto
from dto.catalog_dto import producto_dto, productos_dto
from utils.auth_middleware import admin_global_required

productos_bp = Blueprint('productos_bp', __name__, url_prefix='/api/productos')

@productos_bp.route('', methods=['GET'])
def get_productos():
    productos = Producto.query.filter_by(activo=True).all()
    return jsonify(productos_dto.dump(productos)), 200

@productos_bp.route('', methods=['POST'])
@admin_global_required # Solo Admin Global según HU-011
def create_producto():
    data = request.get_json()
    if not data.get('nombre') or not data.get('precio'):
        return jsonify({'mensaje': 'Nombre y precio son obligatorios'}), 400
        
    nuevo_prod = Producto(
        nombre=data['nombre'], 
        precio=data['precio'], 
        categoria=data.get('categoria')
    )
    db.session.add(nuevo_prod)
    db.session.commit()
    return jsonify(producto_dto.dump(nuevo_prod)), 201

# ====================================================================
# HU-036: ELIMINACIÓN DE PRODUCTOS (SOFT DELETE)
# ====================================================================
@productos_bp.route('/<int:producto_id>', methods=['PATCH'])
@admin_global_required
def desactivar_producto(producto_id):
    producto = Producto.query.get(producto_id)
    if not producto:
        return jsonify({'mensaje': 'Producto no encontrado'}), 404
        
    producto.activo = False
    db.session.commit()
    
    return jsonify({'mensaje': f'El producto {producto.nombre} fue retirado del catálogo operativo.'}), 200