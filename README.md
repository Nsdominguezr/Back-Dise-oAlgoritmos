# Identity Service

Backend de autenticación y gestión de usuarios para el sistema de diseño de algoritmos.

## Tecnologias

- **Flask** - Framework web
- **Flask-SQLAlchemy** - ORM para base de datos MySQL
- **Flask-Marshmallow** - Serialización de datos (DTO)
- **bcrypt** - Hashing de contraseñas
- **PyJWT** - Tokens JWT (access y refresh)
- **PyMySQL** - Conector MySQL
- **pytest** - Pruebas unitarias y de integración

## Estructura del Proyecto

```
identity_service/
├── controllers/
│   └── auth_controller.py  # Endpoints de autenticación
├── dto/
│   └── user_dto.py         # Data Transfer Objects
├── models/
│   └── user_model.py       # Modelos de base de datos
├── tests/
│   └── test_auth.py        # Pruebas automatizadas
├── app.py                  # Aplicación principal
├── config.py               # Configuración
└── requirements.txt       # Dependencias
```

## Instalación

1. Clonar el repositorio
2. Crear entorno virtual e instalar dependencias:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

3. Configurar la base de datos MySQL (`bar_identity_db`) y ajustar `config.py` si es necesario.

4. Ejecutar:

```bash
python app.py
```

El servicio estará disponible en `http://localhost:5001`.

## Endpoints

| Método | Ruta | Descripción | Autenticación |
|--------|------|-------------|---------------|
| POST | `/api/auth/login` | Iniciar sesión | No |
| POST | `/api/auth/refresh` | Renovar access token | No |
| POST | `/api/auth/registro` | Registrar nuevo usuario | Sí (Admin Global) |
| GET | `/api/auth/usuarios` | Listar usuarios | Sí (Admin Global) |

## Autenticación

El servicio utiliza JWT con dos tipos de tokens:

- **Access Token**: Expira en 20 minutos
- **Refresh Token**: Expira en 7 días

Para endpoints protegidos, incluir el header:
```
Authorization: Bearer <access_token>
```

## Roles

- `1` - Admin Global
- `2` - Admin Local
- `3` - Cajero
- `4` - Mesero

## Pruebas

```bash
pytest tests/
```