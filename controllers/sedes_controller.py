"""Módulo de controlador de sedes.

Gestiona las operaciones CRUD de sedes del catálogo.
"""

from flask import Blueprint, request, jsonify
from models.catalog_model import db, Sede
from dto.catalog_dto import sede_dto, sedes_dto
from utils.auth_middleware import admin_global_required

sedes_bp = Blueprint('sedes_bp', __name__, url_prefix='/api/sedes')


@sedes_bp.route('', methods=['GET'])
def get_sedes():
    """Obtiene todas las sedes activas.

    Returns:
        Lista de sedes activas en formato JSON.
    """
    # HU-034: Filtramos para que Angular solo liste las sedes operativas.
    sedes = Sede.query.filter_by(activo=True).all()
    return jsonify(sedes_dto.dump(sedes)), 200


@sedes_bp.route('', methods=['POST'])
@admin_global_required
def create_sede():
    """Crea una nueva sede en el catálogo.

    Args:
        None (datos en JSON: nombre, direccion, telefono).

    Returns:
        Sede creada en formato JSON o mensaje de error.
    """
    data = request.get_json()
    nueva_sede = Sede(
        nombre=data['nombre'],
        direccion=data.get('direccion'),
        telefono=data.get('telefono')
    )
    db.session.add(nueva_sede)
    db.session.commit()
    return jsonify(sede_dto.dump(nueva_sede)), 201


# ====================================================================
# HU-034: ELIMINACIÓN DE SEDES (SOFT DELETE)
# ====================================================================
@sedes_bp.route('/<int:sede_id>', methods=['PATCH'])
@admin_global_required
def desactivar_sede(sede_id):
    """Desactiva (soft delete) una sede del catálogo.

    Args:
        sede_id: ID de la sede a desactivar.

    Returns:
        Mensaje de éxito o error entsprechend.
    """
    sede = Sede.query.get(sede_id)
    if not sede:
        return jsonify({'mensaje': 'Sede no encontrada'}), 404

    sede.activo = False
    db.session.commit()

    return jsonify(
        {'mensaje': f'La sede {sede.nombre} ha sido dada de baja exitosamente.'}
    ), 200