from flask import Blueprint, request, jsonify, current_app
from models.user_model import db, Usuario, Rol 
from dto.user_dto import usuario_dto, usuarios_dto
import bcrypt
import jwt
import datetime
from functools import wraps 

# ==========================================
# CONFIGURACIÓN DEL BLUEPRINT
# ==========================================
# Definimos el Blueprint para modularizar las rutas relacionadas con la autenticación.
# Todas las rutas aquí definidas tendrán el prefijo '/api/auth' (ej. /api/auth/login).
auth_bp = Blueprint('auth_bp', __name__, url_prefix='/api/auth')

# ==========================================
# MIDDLEWARE / DECORADORES DE SEGURIDAD
# ==========================================
def admin_global_required(f):
    """
    Decorador para proteger rutas (HU-006). 
    Verifica que la petición contenga un JWT válido en las cabeceras
    y que el usuario posea estrictamente el rol de 'Admin Global'.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 1. Extraer el token de la cabecera 'Authorization' enviada por Angular
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            # El estándar requiere el formato: "Bearer <token_jwt>"
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]

        # Si no hay token, bloqueamos la petición inmediatamente con código 401 (No autorizado)
        if not token:
            return jsonify({'mensaje': 'Acceso denegado. Token faltante.'}), 401

        try:
            # 2. Desencriptar el token usando la clave secreta de la aplicación
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            
            # 3. VALIDACIÓN ESTRICTA (HU-006): Comprobar el rol dentro del payload del token
            if data.get('rol') != 'Admin Global':
                return jsonify({'mensaje': 'Acceso denegado. Requiere privilegios de Admin Global.'}), 403
                
        except jwt.ExpiredSignatureError:
            # El token caducó (pasaron las horas definidas en el login)
            return jsonify({'mensaje': 'La sesión ha expirado.'}), 401
        except jwt.InvalidTokenError:
            # El token fue alterado maliciosamente o está mal formado
            return jsonify({'mensaje': 'Token inválido o corrupto.'}), 401

        # Si el token es válido y el rol es correcto, permitimos que la función original se ejecute
        return f(*args, **kwargs)
    return decorated

# ==========================================
# CONTROLADORES (ENDPOINTS)
# ==========================================

@auth_bp.route('/usuarios', methods=['GET'])
@admin_global_required # <-- NUEVO: Ahora esta ruta está protegida. Solo el Admin Global puede listar usuarios.
def get_usuarios():
    """
    Endpoint protegido para obtener la lista de todos los usuarios registrados.
    Requiere un JWT válido de un Administrador Global en los encabezados.
    """
    # 1. Lógica del Modelo: Consultar todos los registros usando el ORM SQLAlchemy
    usuarios = Usuario.query.all()
    
    # 2. Lógica DTO: Serializar los objetos a JSON.
    # El DTO se encarga de que la respuesta sea segura y no incluya contraseñas.
    resultado = usuarios_dto.dump(usuarios)
    
    # 3. Respuesta del Controlador con los datos serializados
    return jsonify(resultado), 200


@auth_bp.route('/registro', methods=['POST'])
@admin_global_required # <-- Protege la ruta: Solo un Admin Global autenticado puede ejecutar esto
def registrar_usuario():
    """
    Endpoint para registrar un nuevo usuario en el sistema.
    """
    data = request.get_json()
    
    # 1. Validar que el JSON no venga vacío y traiga los campos mínimos requeridos
    if not data or not data.get('username') or not data.get('password') or not data.get('rol_id') or not data.get('sede_id'):
        return jsonify({'mensaje': 'Faltan datos obligatorios'}), 400

    # 2. VALIDACIÓN DE MODELO ESTRICTO DE ROLES (HU-005)
    # Consultamos si el ID del rol enviado realmente existe en la tabla 'roles'
    rol_existente = Rol.query.get(data['rol_id'])
    if not rol_existente:
        return jsonify({'mensaje': 'Rol inválido. Asigne un rol permitido (1: Admin Global, 2: Admin Local, 3: Cajero, 4: Mesero)'}), 400

    # 3. Hashing de contraseña (HU-004)
    # Convertimos el string a bytes (utf-8), lo encriptamos con bcrypt y generamos un "salt" dinámico
    hashed_pw = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())

    # 4. Crear la instancia del Modelo Usuario con los datos validados y la clave encriptada
    nuevo_usuario = Usuario(
        username=data['username'],
        password_hash=hashed_pw.decode('utf-8'), # Guardamos el hash como string
        rol_id=data['rol_id'],
        sede_id=data['sede_id']
    )

    try:
        # Intentar guardar en la base de datos MySQL
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        # Devolver el usuario recién creado usando el DTO para ocultar la clave
        return usuario_dto.jsonify(nuevo_usuario), 201
    except Exception as e:
        # Si falla (ej. por username duplicado debido a la restricción 'unique=True'), revertimos la transacción
        db.session.rollback()
        return jsonify({'mensaje': 'Error al crear usuario, es posible que el username ya exista.'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Endpoint público para autenticar a los usuarios y emitir tokens JWT (HU-007).
    """
    data = request.get_json()
    
    # 1. Validar presencia de credenciales en el request
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'mensaje': 'Faltan credenciales'}), 400

    # 2. Buscar al usuario en la base de datos por su username
    usuario = Usuario.query.filter_by(username=data['username']).first()

    # Si el usuario no se encuentra, devolvemos error 401
    if not usuario:
        return jsonify({'mensaje': 'Usuario o contraseña incorrectos'}), 401

    # 3. Verificar contraseña contra el Hash guardado en la BD
    password_ingresada = data['password'].encode('utf-8')
    password_guardada = usuario.password_hash.encode('utf-8')
    
    # bcrypt compara la contraseña en texto plano con el hash de manera segura
    password_valida = bcrypt.checkpw(password_ingresada, password_guardada)
    
    if password_valida:
        # --- GENERACIÓN DE ACCESS TOKEN (Vida corta para pruebas) ---
        fecha_expiracion_access = datetime.datetime.utcnow() + datetime.timedelta(minutes=20)
        
        # 4. Construir el Payload (cuerpo) del JWT con la información de la sesión
        token_payload = {
            'user_id': usuario.id,
            'rol': usuario.rol.nombre, # Extraemos el nombre del rol gracias a la relación en el modelo
            'sede_id': usuario.sede_id,
            'exp': fecha_expiracion_access 
        }
        
        # 5. Firmar criptográficamente el Access Token
        access_token = jwt.encode(token_payload, current_app.config['SECRET_KEY'], algorithm='HS256')

        # --- GENERACIÓN DE REFRESH TOKEN (Vida larga: 7 días) ---
        fecha_expiracion_refresh = datetime.datetime.utcnow() + datetime.timedelta(days=7)
        refresh_payload = {
            'user_id': usuario.id,
            'type': 'refresh', # Etiqueta para diferenciarlo del access token
            'exp': fecha_expiracion_refresh
        }
        refresh_token = jwt.encode(refresh_payload, current_app.config['SECRET_KEY'], algorithm='HS256')

        # 6. Retornar los tokens y los datos limpios del usuario al frontend
        return jsonify({
            'mensaje': 'Login exitoso',
            'token': access_token,
            'refresh_token': refresh_token,
            'expira_en': fecha_expiracion_access.isoformat() + 'Z',
            'usuario': usuario_dto.dump(usuario)
        }), 200
        
    else:
        # Si la contraseña no coincide, devolvemos error 401 de forma genérica por seguridad
        return jsonify({'mensaje': 'Usuario o contraseña incorrectos'}), 401


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """
    Endpoint para renovar el Access Token usando un Refresh Token válido.
    """
    data = request.get_json()
    
    if not data or not data.get('refresh_token'):
        return jsonify({'mensaje': 'Se requiere el refresh_token'}), 400

    refresh_token_recibido = data.get('refresh_token')

    try:
        # 1. Desencriptar el Refresh Token
        payload = jwt.decode(refresh_token_recibido, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        
        # 2. Validar que sea un token de tipo 'refresh'
        if payload.get('type') != 'refresh':
            return jsonify({'mensaje': 'Token inválido para renovación.'}), 401
            
        # 3. Verificar existencia del usuario
        usuario = Usuario.query.get(payload['user_id'])
        if not usuario:
            return jsonify({'mensaje': 'Usuario no encontrado.'}), 401
            
        # 4. Generar nuevo Access Token (otros 2 minutos para seguir probando)
        nueva_fecha_exp = datetime.datetime.utcnow() + datetime.timedelta(minutes=20)
        nuevo_payload = {
            'user_id': usuario.id,
            'rol': usuario.rol.nombre,
            'sede_id': usuario.sede_id,
            'exp': nueva_fecha_exp 
        }
        nuevo_access_token = jwt.encode(nuevo_payload, current_app.config['SECRET_KEY'], algorithm='HS256')
        
        # 5. Retornar nueva llave de acceso
        return jsonify({
            'mensaje': 'Token renovado exitosamente',
            'token': nuevo_access_token,
            'expira_en': nueva_fecha_exp.isoformat() + 'Z'
        }), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({'mensaje': 'El Refresh Token ha expirado. Inicie sesión nuevamente.'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'mensaje': 'Refresh Token inválido o corrupto.'}), 401