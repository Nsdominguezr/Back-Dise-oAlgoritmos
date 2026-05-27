"""Módulo de controlador de productos.

Gestiona las operaciones CRUD de productos del catálogo.
"""

from flask import Blueprint, request, jsonify
from models.catalog_model import db, Producto
from dto.catalog_dto import producto_dto, productos_dto
from utils.auth_middleware import admin_global_required

productos_bp = Blueprint('productos_bp', __name__, url_prefix='/api/productos')


# ====================================================================
# ALGORITMO: ORDENAMIENTO RÁPIDO (QUICK SORT)
# ====================================================================
def ordenamiento_rapido(arreglo):
    """Ordena un arreglo usando el algoritmo Quick Sort.

    Implementa el método divide y conquista,
    seleccionando un pivote y分区ando el arreglo.

    Args:
        arreglo: Lista de elementos comparables.

    Returns:
        Lista ordenada de menor a mayor.
    """
    if len(arreglo) <= 1:
        return arreglo
    pivote = arreglo[len(arreglo) // 2]
    izquierda = [x for x in arreglo if x < pivote]
    medio = [x for x in arreglo if x == pivote]
    derecha = [x for x in arreglo if x > pivote]
    return ordenamiento_rapido(izquierda) + medio + ordenamiento_rapido(derecha)


# ====================================================================
# ENDPOINTS
# ====================================================================
@productos_bp.route('', methods=['GET'])
def get_productos():
    """Obtiene todos los productos activos ordenados por precio.

    Returns:
        Lista de productos en formato JSON, ordenados de menor a mayor precio.
    """
    productos = Producto.query.filter_by(activo=True).all()

    # Ordenar por precio usando Quick Sort (menor a mayor).
    precios_productos = [(float(p.precio), p) for p in productos]

    # Ordenar solo los precios.
    precios_ordenados = ordenamiento_rapido([precio for precio, _ in precios_productos])

    # Reconstruir lista de productos en orden.
    productos_ordenados = []
    for precio in precios_ordenados:
        for prec, prod in precios_productos:
            if prec == precio and prod not in productos_ordenados:
                productos_ordenados.append(prod)
                break

    return jsonify(productos_dto.dump(productos_ordenados)), 200


@productos_bp.route('', methods=['POST'])
@admin_global_required
def create_producto():
    """Crea un nuevo producto en el catálogo.

    Args:
        None (datos en JSON: nombre, precio, categoria).

    Returns:
        Producto creado en formato JSON o mensaje de error.
    """
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
    """Desactiva (soft delete) un producto del catálogo.

    Args:
        producto_id: ID del producto a desactivar.

    Returns:
        Mensaje de éxito o error entsprechend.
    """
    producto = Producto.query.get(producto_id)
    if not producto:
        return jsonify({'mensaje': 'Producto no encontrado'}), 404

    producto.activo = False
    db.session.commit()

    return jsonify(
        {'mensaje': f'El producto {producto.nombre} fue retirado del catálogo operativo.'}
    ), 200