# Identity Service — Microservicio de Autenticación y Gestión de Identidades

## Propósito

API REST centralizada para la autenticación de usuarios y gestión de identidades. Provee login con JWT, registro de usuarios y control de acceso basado en roles (RBAC). Acts as the **security layer** for the entire microservices architecture.

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                    Angular (Frontend)                    │
└─────────────────────────┬───────────────────────────────┘
                          │  HTTP/REST + JWT
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   Identity Service                       │
│                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────┐ │
│  │ Controllers  │───▶│   Models     │───▶│   MySQL   │ │
│  │  (Routes)    │    │ (SQLAlchemy) │    │   (DB)    │ │
│  └──────┬───────┘    └──────────────┘    └───────────┘ │
│         │                                              │
│         ▼                                              │
│  ┌──────────────┐    ┌──────────────┐                  │
│  │     DTO      │◀───│  Response    │                  │
│  │(Marshmallow) │    │   (JSON)     │                  │
│  └──────────────┘    └──────────────┘                  │
└─────────────────────────────────────────────────────────┘
```

### Flujo de Petición Protegida

1. Frontend envía request con `Authorization: Bearer <token>`
2. Decorador `@admin_global_required` intercepta y valida JWT
3. Si válido, el controlador procesa la solicitud
4. DTO serializa respuesta (excluyendo passwords)
5. JSON devuelto al frontend

---

## Stack Tecnológico

| Tecnología            | Propósito                               |
|-----------------------|-----------------------------------------|
| Flask 3.0.2           | Framework web / API                     |
| Flask-SQLAlchemy 3.1.1| ORM para MySQL                          |
| Flask-Marshmallow 1.2.1| Serialización DTOs                      |
| bcrypt 4.1.2          | Hashing de contraseñas (Bcrypt)         |
| PyJWT 2.8.0           | Tokens JWT (access + refresh)           |
| PyMySQL 1.1.0         | Conector MySQL                          |
| pytest 8.1.1          | Pruebas unitarias y de integración     |

---

## Estructura del Proyecto

```
identity_service/
├── controllers/
│   └── auth_controller.py    # Endpoints y lógica de negocio
├── dto/
│   └── user_dto.py           # Serialización (exclusión de password_hash)
├── models/
│   └── user_model.py         # Modelos SQLAlchemy (Usuario, Rol)
├── tests/
│   └── test_auth.py          # Pruebas unitarias y de integración
├── app.py                    # Factory de la aplicación Flask
├── config.py                 # Configuración de entorno
└── requirements.txt         # Dependencias Python
```

---

## Modelo de Datos

### Rol

| Campo  | Tipo         | Descripción                |
|--------|--------------|----------------------------|
| id     | Integer (PK) | Identificador único         |
| nombre | String(50)   | Nombre del rol (único)     |

### Usuario

| Campo          | Tipo         | Descripción                   |
|----------------|--------------|--------------------------------|
| id             | Integer (PK) | Identificador único            |
| username       | String(50)   | Username (único)               |
| password_hash  | String(255)  | Hash bcrypt de la contraseña   |
| rol_id         | Integer (FK) | Referencia a roles.id         |
| sede_id        | Integer      | ID de la sede asignada        |
| creado_en      | DateTime     | Fecha de creación              |

### Roles del Sistema

| ID  | Nombre       |
|-----|--------------|
| 1   | Admin Global |
| 2   | Admin Local  |
| 3   | Cajero       |
| 4   | Mesero       |

---

## API Endpoints

### Endpoints Públicos

#### POST `/api/auth/login`
Inicia sesión y devuelve tokens JWT.

**Request:**
```json
{
  "username": "admin",
  "password": "miClaveSegura123"
}
```

**Response (200):**
```json
{
  "mensaje": "Login exitoso",
  "token": "<access_token_jwt>",
  "refresh_token": "<refresh_token_jwt>",
  "expira_en": "2026-04-24T10:20:00Z",
  "usuario": {
    "id": 1,
    "username": "admin",
    "rol": { "id": 1, "nombre": "Admin Global" },
    "sede_id": 1
  }
}
```

#### POST `/api/auth/refresh`
Renueva el access token usando un refresh token válido.

**Request:**
```json
{
  "refresh_token": "<refresh_token_jwt>"
}
```

---

### Endpoints Protegidos (Requieren `Authorization: Bearer <token>`)

| Método | Endpoint              | Rol Requerido   | Descripción                |
|--------|-----------------------|-----------------|----------------------------|
| GET    | `/api/auth/usuarios`  | Admin Global    | Lista todos los usuarios   |
| POST   | `/api/auth/registro`  | Admin Global    | Crea un nuevo usuario      |

---

## Autenticación y Autorización

### Tokens JWT

| Token          | Expiración | Contenido                        |
|----------------|------------|----------------------------------|
| Access Token   | 20 min     | user_id, rol, sede_id            |
| Refresh Token  | 7 días     | user_id, type: "refresh"          |

### Decorador de Autorización

`@admin_global_required` es un middleware que:
1. Extrae el token del header `Authorization: Bearer <token>`
2. Valida firma y expiración del JWT
3. Verifica que el rol sea **Admin Global**
4. Bloquea con 401/403 si la validación falla

### Códigos de Error

| Código | Significado                                |
|--------|---------------------------------------------|
| 400    | Datos faltantes o inválidos                 |
| 401    | Token faltante, inválido o expirado         |
| 403    | Token válido pero sin permisos suficientes   |
| 500    | Error interno del servidor                  |

---

## Instalación Local

### Requisitos

- Python 3.10+
- MySQL 8.0+ (base de datos: `bar_identity_db`)

### Pasos

```bash
# Clonar y crear entorno virtual
git clone <repo_url>
cd identity_service
python -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Crear base de datos
CREATE DATABASE bar_identity_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Configurar variables de entorno
export DATABASE_URL='mysql+pymysql://root:tu_password@localhost/bar_identity_db'
export SECRET_KEY='tu-clave-secreta-muy-larga-y-aleatoria'

# Iniciar servicio
python app.py
```

Disponible en: `http://localhost:5001`

---

## Ejecución de Pruebas

```bash
# Todas las pruebas
pytest tests/ -v

# Unitarias específicas
pytest tests/test_auth.py::test_hashing_bcrypt -v
pytest tests/test_auth.py::test_generacion_y_validacion_jwt -v

# Integración
python -m pytest tests/test_auth.py::test_login_integracion_fallido -v
```

Las pruebas de integración usan **SQLite en memoria** para no afectar la base de datos de desarrollo.

---

## Despliegue en Producción

### Docker Compose (Recomendado)

```yaml
version: '3.8'
services:
  identity_db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root_password
      MYSQL_DATABASE: bar_identity_db
    volumes:
      - mysql_data:/var/lib/mysql

  identity_service:
    build: .
    ports:
      - "5001:5001"
    environment:
      DATABASE_URL: mysql+pymysql://root:root_password@identity_db:3306/bar_identity_db
      SECRET_KEY: ${SECRET_KEY}
    depends_on:
      - identity_db
```

### Gunicorn + Systemd

```ini
[Unit]
Description=Identity Service Flask API
After=network.target mysql.service

[Service]
Type=simple
User=identity_service
WorkingDirectory=/var/www/identity_service
EnvironmentFile=/var/www/identity_service/.env
ExecStart=/var/www/identity_service/venv/bin/gunicorn \
    --workers 4 --bind 127.0.0.1:5001 --timeout 120 \
    app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## Checklist de Producción

- [ ] Variables de entorno: `SECRET_KEY` generado con `openssl rand -hex 64`
- [ ] Base de datos: Usuario app dedicado, no root
- [ ] HTTPS: Siempre habilitado (SSL/TLS)
- [ ] Gunicorn: Mínimo 4 workers, timeout configurado
- [ ] Logs: Rotación configurada (logrotate)
- [ ] Firewall: Solo puertos 80/443 expuestos
- [ ] Backups: Automatizar backup de la base de datos
- [ ] Health check: Endpoint `/api/auth/login` disponible

---

*Proprietary — Todos los derechos reservados.*
