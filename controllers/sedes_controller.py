from flask import Blueprint, request, jsonify
from models.catalog_model import db, Sede
from dto.catalog_dto import sede_dto, sedes_dto
from utils.auth_middleware import admin_global_required

sedes_bp = Blueprint('sedes_bp', __name__, url_prefix='/api/sedes')

@sedes_bp.route('', methods=['GET'])
def get_sedes():
    sedes = Sede.query.all()
    return jsonify(sedes_dto.dump(sedes)), 200

@sedes_bp.route('', methods=['POST'])
@admin_global_required # Solo Admin Global según HU-009
def create_sede():
    data = request.get_json()
    nueva_sede = Sede(
        nombre=data['nombre'], 
        direccion=data.get('direccion'), 
        telefono=data.get('telefono')
    )
    db.session.add(nueva_sede)
    db.session.commit()
    return jsonify(sede_dto.dump(nueva_sede)), 201