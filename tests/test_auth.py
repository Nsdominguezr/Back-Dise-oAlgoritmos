import pytest
import bcrypt
import jwt
import datetime
from app import create_app, db

# ==========================================
# 1. PRUEBAS UNITARIAS (Aisladas, sin BD)
# ==========================================
def test_hashing_bcrypt():
    """Prueba Unitaria: Verifica que el hashing y la validación funcionen correctamente"""
    password_plana = "MiClaveSegura123".encode('utf-8')
    
    # Simular registro (Hashear)
    hashed_pw = bcrypt.hashpw(password_plana, bcrypt.gensalt())
    
    # Validar que el checkpw devuelva True para la clave correcta
    assert bcrypt.checkpw(password_plana, hashed_pw) == True
    
    # Validar que devuelva False para una clave incorrecta
    assert bcrypt.checkpw("ClaveMala".encode('utf-8'), hashed_pw) == False

def test_generacion_y_validacion_jwt():
    """Prueba Unitaria: Verifica que el token JWT se firme y desencripte bien"""
    secret_key = "clave_secreta_de_prueba"
    payload = {
        'user_id': 1,
        'rol': 'Admin Global',
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    
    # Firmar token
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    assert token is not None
    
    # Desencriptar token
    decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
    assert decoded['user_id'] == 1
    assert decoded['rol'] == 'Admin Global'


# ==========================================
# 2. PRUEBA DE INTEGRACIÓN (Simulando HTTP)
# ==========================================
@pytest.fixture
def client():
    """Configuración del cliente de pruebas aislando la base de datos"""
    # 1. Creamos una instancia de la app exclusiva para pruebas
    app_test = create_app()
    app_test.config['TESTING'] = True
    
    # 2. PRO-TIP: Usamos SQLite en memoria para no tocar tu MySQL durante las pruebas
    app_test.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    # 3. Levantamos el cliente de pruebas
    with app_test.test_client() as client:
        with app_test.app_context():
            db.create_all() # Crea las tablas en la BD temporal
            yield client
            db.drop_all()   # Limpia la BD temporal al terminar

def test_login_integracion_fallido(client):
    """Prueba Integración: Petición HTTP POST a /login con datos falsos"""
    # Enviamos un request real al endpoint
    response = client.post('/api/auth/login', json={
        "username": "usuario_que_no_existe_999",
        "password": "clave_inventada"
    })
    
    # Verificar que el Criterio de Aceptación se cumple: "Fallido devuelve error 401"
    assert response.status_code == 401
    
    # Verificar que el mensaje en el JSON es el correcto
    json_data = response.get_json()
    assert json_data['mensaje'] == 'Usuario o contraseña incorrectos'