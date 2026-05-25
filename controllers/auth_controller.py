from flask import Blueprint, request, jsonify, current_app
from models.user_model import db, Usuario, Rol 
from dto.user_dto import usuario_dto, usuarios_dto
import bcrypt
import jwt
import datetime
from functools import wraps 

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/api/auth')

# ==========================================
# MIDDLEWARE / DECORADORES DE SEGURIDAD
# ==========================================
def admin_global_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({'mensaje': 'Acceso denegado. Token faltante.'}), 401

        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            if data.get('rol') != 'Admin Global':
                return jsonify({'mensaje': 'Acceso denegado. Requiere privilegios de Admin Global.'}), 403
        except jwt.ExpiredSignatureError:
            return jsonify({'mensaje': 'La sesión ha expirado.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'mensaje': 'Token inválido o corrupto.'}), 401

        return f(*args, **kwargs)
    return decorated

# ==========================================
# CONTROLADORES (ENDPOINTS)
# ==========================================

@auth_bp.route('/usuarios', methods=['GET'])
@admin_global_required
def get_usuarios():
    # Retornamos TODOS los usuarios (activos e inactivos) para que el Admin pueda ver el historial completo
    usuarios = Usuario.query.all()
    resultado = usuarios_dto.dump(usuarios)
    return jsonify(resultado), 200

@auth_bp.route('/registro', methods=['POST'])
@admin_global_required
def registrar_usuario():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password') or not data.get('rol_id') or not data.get('sede_id'):
        return jsonify({'mensaje': 'Faltan datos obligatorios'}), 400

    rol_existente = Rol.query.get(data['rol_id'])
    if not rol_existente:
        return jsonify({'mensaje': 'Rol inválido.'}), 400

    hashed_pw = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())

    nuevo_usuario = Usuario(
        username=data['username'],
        password_hash=hashed_pw.decode('utf-8'),
        rol_id=data['rol_id'],
        sede_id=data['sede_id']
        # El campo 'activo' se pone en True por defecto gracias al modelo
    )

    try:
        db.session.add(nuevo_usuario)
        db.session.commit()
        return usuario_dto.jsonify(nuevo_usuario), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'mensaje': 'Error al crear usuario, es posible que el username ya exista.'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'mensaje': 'Faltan credenciales'}), 400

    usuario = Usuario.query.filter_by(username=data['username']).first()

    if not usuario:
        return jsonify({'mensaje': 'Usuario o contraseña incorrectos'}), 401

    # ==========================================================
    # HU-035: BLOQUEO DE SEGURIDAD PARA USUARIOS DESACTIVADOS
    # ==========================================================
    if not usuario.activo:
        return jsonify({'mensaje': 'Cuenta suspendida o inactiva. Contacte al administrador.'}), 403

    password_ingresada = data['password'].encode('utf-8')
    password_guardada = usuario.password_hash.encode('utf-8')
    password_valida = bcrypt.checkpw(password_ingresada, password_guardada)
    
    if password_valida:
        fecha_expiracion_access = datetime.datetime.utcnow() + datetime.timedelta(minutes=20)
        token_payload = {
            'user_id': usuario.id,
            'rol': usuario.rol.nombre,
            'sede_id': usuario.sede_id,
            'exp': fecha_expiracion_access 
        }
        access_token = jwt.encode(token_payload, current_app.config['SECRET_KEY'], algorithm='HS256')

        fecha_expiracion_refresh = datetime.datetime.utcnow() + datetime.timedelta(days=7)
        refresh_payload = {
            'user_id': usuario.id,
            'type': 'refresh',
            'exp': fecha_expiracion_refresh
        }
        refresh_token = jwt.encode(refresh_payload, current_app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({
            'mensaje': 'Login exitoso',
            'token': access_token,
            'refresh_token': refresh_token,
            'expira_en': fecha_expiracion_access.isoformat() + 'Z',
            'usuario': usuario_dto.dump(usuario)
        }), 200
    else:
        return jsonify({'mensaje': 'Usuario o contraseña incorrectos'}), 401


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    data = request.get_json()
    if not data or not data.get('refresh_token'):
        return jsonify({'mensaje': 'Se requiere el refresh_token'}), 400

    refresh_token_recibido = data.get('refresh_token')

    try:
        payload = jwt.decode(refresh_token_recibido, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        if payload.get('type') != 'refresh':
            return jsonify({'mensaje': 'Token inválido para renovación.'}), 401
            
        usuario = Usuario.query.get(payload['user_id'])
        if not usuario:
            return jsonify({'mensaje': 'Usuario no encontrado.'}), 401
            
        # ==========================================================
        # HU-035: BLOQUEO AL RENOVAR EL TOKEN
        # ==========================================================
        if not usuario.activo:
            return jsonify({'mensaje': 'La cuenta ha sido suspendida durante su sesión.'}), 403
            
        nueva_fecha_exp = datetime.datetime.utcnow() + datetime.timedelta(minutes=20)
        nuevo_payload = {
            'user_id': usuario.id,
            'rol': usuario.rol.nombre,
            'sede_id': usuario.sede_id,
            'exp': nueva_fecha_exp 
        }
        nuevo_access_token = jwt.encode(nuevo_payload, current_app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'mensaje': 'Token renovado exitosamente',
            'token': nuevo_access_token,
            'expira_en': nueva_fecha_exp.isoformat() + 'Z'
        }), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({'mensaje': 'El Refresh Token ha expirado. Inicie sesión nuevamente.'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'mensaje': 'Refresh Token inválido o corrupto.'}), 401


# ====================================================================
# HU-035: ELIMINACIÓN DE USUARIOS (SOFT DELETE)
# ====================================================================
@auth_bp.route('/usuarios/<int:usuario_id>/desactivar', methods=['PATCH'])
@admin_global_required
def desactivar_usuario(usuario_id):
    """Baja lógica de un empleado. El usuario no se borra, pero no podrá hacer login."""
    usuario = Usuario.query.get(usuario_id)
    
    if not usuario:
        return jsonify({'mensaje': 'Usuario no encontrado'}), 404
        
    # Impedir que un admin se desactive a sí mismo accidentalmente
    # Si quieres implementar esto más riguroso, deberías extraer el ID del JWT del token entrante
    if usuario.rol.nombre == 'Admin Global':
        return jsonify({'mensaje': 'Advertencia: No puedes desactivar a un Admin Global desde aquí.'}), 400
        
    usuario.activo = False
    db.session.commit()
    
    return jsonify({'mensaje': f'El usuario {usuario.username} ha sido dado de baja. Se ha revocado su acceso.'}), 200