from flask import Blueprint, request, jsonify, current_app
from models.user_model import db, Usuario
from dto.user_dto import usuario_dto, usuarios_dto
import bcrypt
import jwt
import datetime

# Definición del Blueprint para las rutas de autenticación/usuarios
auth_bp = Blueprint('auth_bp', __name__, url_prefix='/api/auth')

@auth_bp.route('/usuarios', methods=['GET'])
def get_usuarios():
    # 1. Lógica del Modelo: Consultar base de datos
    usuarios = Usuario.query.all()
    # 2. Lógica DTO: Serializar a JSON seguro (sin contraseñas)
    resultado = usuarios_dto.dump(usuarios)
    # 3. Respuesta del Controlador
    return jsonify(resultado), 200

@auth_bp.route('/registro', methods=['POST'])
def registrar_usuario():
    data = request.get_json()
    
    # Validaciones básicas
    if not data or not data.get('username') or not data.get('password') or not data.get('rol_id') or not data.get('sede_id'):
        return jsonify({'mensaje': 'Faltan datos obligatorios'}), 400

    # Hashing de contraseña (Requerimiento de seguridad)
    hashed_pw = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())

    # 1. Lógica del Modelo: Crear nueva instancia
    nuevo_usuario = Usuario(
        username=data['username'],
        password_hash=hashed_pw.decode('utf-8'),
        rol_id=data['rol_id'],
        sede_id=data['sede_id']
    )

    try:
        db.session.add(nuevo_usuario)
        db.session.commit()
        # 2. Lógica DTO: Retornar el usuario creado formateado
        return usuario_dto.jsonify(nuevo_usuario), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'mensaje': 'Error al crear usuario, es posible que el username ya exista.'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # 1. Validar que vengan los datos
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'mensaje': 'Faltan credenciales'}), 400

    # 2. Buscar usuario en base de datos
    usuario = Usuario.query.filter_by(username=data['username']).first()

    # Si no existe el usuario, devolvemos 401 Unauthorized
    if not usuario:
        return jsonify({'mensaje': 'Usuario o contraseña incorrectos'}), 401

    # 3. Verificar contraseña contra el Hash guardado
    password_ingresada = data['password'].encode('utf-8')
    password_guardada = usuario.password_hash.encode('utf-8')
    
    password_valida = bcrypt.checkpw(password_ingresada, password_guardada)
    
    if password_valida:
        # 4. Generar el payload del JWT
        token_payload = {
            'user_id': usuario.id,
            'rol': usuario.rol.nombre, # Requiere que la relación esté definida en el modelo
            'sede_id': usuario.sede_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=8) # Expira en 8 horas
        }
        
        # 5. Firmar el token con la clave secreta
        token = jwt.encode(token_payload, current_app.config['SECRET_KEY'], algorithm='HS256')

        # 6. Retornar respuesta exitosa
        return jsonify({
            'mensaje': 'Login exitoso',
            'token': token,
            'usuario': usuario_dto.dump(usuario)
        }), 200
        
    else:
        return jsonify({'mensaje': 'Usuario o contraseña incorrectos'}), 401