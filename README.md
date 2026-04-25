# Identity Service

API REST de autenticación y gestión de usuarios. Provee login con JWT, registro de usuarios y control de acceso basado en roles (RBAC).

---

## Tabla de Contenidos

- [Tecnologías](#tecnologías)
- [Arquitectura](#arquitectura)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Modelos de Datos](#modelos-de-datos)
- [API Endpoints](#api-endpoints)
- [Autenticación y Autorización](#autenticación-y-autorización)
- [Instalación Local](#instalación-local)
- [Ejecución de Pruebas](#ejecución-de-pruebas)
- [Despliegue en Producción](#despliegue-en-producción)

---

## Tecnologías

| Tecnología | Propósito |
|------------|-----------|
| Flask 3.0.2 | Framework web / API |
| Flask-SQLAlchemy 3.1.1 | ORM para MySQL |
| Flask-Marshmallow 1.2.1 | Serialización DTOs |
| bcrypt 4.1.2 | Hashing de contraseñas (seguro) |
| PyJWT 2.8.0 | Tokens JWT (access + refresh) |
| PyMySQL 1.1.0 | Conector MySQL |
| pytest 8.1.1 | Pruebas unitarias y de integración |

---

## Arquitectura

El servicio sigue el patrón **MVC (Model-View-Controller)** adaptado a Flask:

```
┌─────────────────────────────────────────────────────────┐
│                      Angular (Frontend)                  │
└─────────────────────────┬───────────────────────────────┘
                          │  HTTP/REST + JWT
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   Identity Service                       │
│                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │ Controllers  │───▶│    Models    │───▶│     DB     │ │
│  │  (Routes)    │    │  (SQLAlchemy)│    │   MySQL    │ │
│  └──────┬───────┘    └──────────────┘    └────────────┘ │
│         │                                               │
│         ▼                                               │
│  ┌──────────────┐    ┌──────────────┐                   │
│  │     DTO      │◀───│   Response   │                   │
│  │ (Marshmallow)│    │   (JSON)    │                   │
│  └──────────────┘    └──────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

**Flujo de una petición protegida:**
1. Angular envía请求 con `Authorization: Bearer <token>`
2. El decorador `@admin_global_required` intercepta y valida el JWT
3. Si es válido, el controlador procesa la solicitud
4. El DTO serializa la respuesta (excluyendo contraseñas)
5. Se devuelve JSON al frontend

---

## Estructura del Proyecto

```
identity_service/
├── controllers/
│   └── auth_controller.py   # Endpoints y lógica de negocio
├── dto/
│   └── user_dto.py          # Serialización (exclusion de password_hash)
├── models/
│   └── user_model.py        # Modelos SQLAlchemy (Usuario, Rol)
├── tests/
│   └── test_auth.py         # Pruebas unitarias y de integración
├── app.py                    # Factory de la aplicación Flask
├── config.py                 # Configuración de entorno
└── requirements.txt         # Dependencias Python
```

---

## Modelos de Datos

### Rol
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer | PK |
| nombre | String(50) | Nombre del rol (único) |

### Usuario
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer | PK |
| username | String(50) | Username (único) |
| password_hash | String(255) | Hash bcrypt de la contraseña |
| rol_id | Integer | FK → roles.id |
| sede_id | Integer | ID de la sede |
| creado_en | DateTime | Fecha de creación |

### Roles del Sistema
| ID | Nombre |
|----|--------|
| 1 | Admin Global |
| 2 | Admin Local |
| 3 | Cajero |
| 4 | Mesero |

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

**Response (200):**
```json
{
  "mensaje": "Token renovado exitosamente",
  "token": "<nuevo_access_token>",
  "expira_en": "2026-04-24T10:40:00Z"
}
```

---

### Endpoints Protegidos (Requieren `Authorization: Bearer <token>`)

#### GET `/api/auth/usuarios`
Lista todos los usuarios. Solo accesible por **Admin Global**.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
[
  {
    "id": 1,
    "username": "admin",
    "rol": { "id": 1, "nombre": "Admin Global" },
    "sede_id": 1,
    "creado_en": "2026-04-24T08:00:00"
  }
]
```

#### POST `/api/auth/registro`
Crea un nuevo usuario. Solo accesible por **Admin Global**.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "username": "nuevo_usuario",
  "password": "ClaveSegura456",
  "rol_id": 3,
  "sede_id": 2
}
```

**Response (201):**
```json
{
  "id": 5,
  "username": "nuevo_usuario",
  "rol": { "id": 3, "nombre": "Cajero" },
  "sede_id": 2,
  "creado_en": "2026-04-24T10:00:00"
}
```

---

## Autenticación y Autorización

### Tokens JWT

El servicio utiliza **dos tokens** para maximizar seguridad y usabilidad:

| Token | Expiración | Contenido |
|-------|------------|-----------|
| Access Token | 20 minutos | user_id, rol, sede_id |
| Refresh Token | 7 días | user_id, type: "refresh" |

### Decorador de Autorización

`@admin_global_required` es un middleware que:
1. Extrae el token del header `Authorization: Bearer <token>`
2. Valida la firma y expiración del JWT
3. Verifica que el rol sea **Admin Global**
4. Bloquea con 401/403 si la validación falla

### Códigos de Error Comunes

| Código | Significado |
|--------|-------------|
| 400 | Datos faltantes o inválidos en la petición |
| 401 | Token faltante, inválido o expirado |
| 403 | Token válido pero sin permisos suficientes |
| 500 | Error interno del servidor |

---

## Instalación Local

### Prerrequisitos
- Python 3.10+
- MySQL 8.0+ (base de datos: `bar_identity_db`)

### Pasos

**1. Clonar y crear entorno virtual**
```bash
git clone <repo_url>
cd identity_service
python -m venv venv
source venv/bin/activate      # Linux/Mac
# venv\Scripts\activate       # Windows
```

**2. Instalar dependencias**
```bash
pip install -r requirements.txt
```

**3. Configurar base de datos MySQL**
```sql
CREATE DATABASE bar_identity_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

**4. Configurar variables de entorno**
```bash
export DATABASE_URL='mysql+pymysql://root:tu_password@localhost/bar_identity_db'
export SECRET_KEY='tu-clave-secreta-muy-larga-y-aleatoria'
```

**5. Iniciar el servicio**
```bash
python app.py
```

El servicio estará disponible en: `http://localhost:5001`

---

## Ejecución de Pruebas

```bash
# Todas las pruebas
pytest tests/ -v

# Solo integración ( requiere app )
python -m pytest tests/test_auth.py::test_login_integracion_fallido -v

# Solo unitarias
python -m pytest tests/test_auth.py::test_hashing_bcrypt -v
python -m pytest tests/test_auth.py::test_generacion_y_validacion_jwt -v
```

Las pruebas de integración usan **SQLite en memoria** para no afectar la base de datos de desarrollo.

---

## Despliegue en Producción

### Opción 1: Servidor Tradicional (Gunicorn + Nginx)

**1. Preparar el servidor**
```bash
# Instalar dependencias del sistema
sudo apt update && sudo apt install -y python3-venv nginx mysql-server

# Crear usuario para el servicio
sudo useradd -m -s /bin/bash identity_service
sudo mkdir -p /var/www/identity_service
sudo chown identity_service:identity_service /var/www/identity_service
```

**2. Desplegar código**
```bash
# En tu máquina local, empaquetar
tar -czvf identity_service.tar.gz \
  controllers/ dto/ models/ tests/ \
  app.py config.py requirements.txt

# Transferir al servidor y descomprimir
scp identity_service.tar.gz user@servidor:/tmp/
ssh user@servidor
sudo tar -xzvf /tmp/identity_service.tar.gz -C /var/www/identity_service/
sudo chown -R identity_service:identity_service /var/www/identity_service
```

**3. Configurar entorno**
```bash
sudo -u identity_service bash -c 'cd /var/www/identity_service && python3 -m venv venv'
sudo -u identity_service /var/www/identity_service/venv/bin/pip install -r /var/www/identity_service/requirements.txt

# Variables de entorno (production)
cat > /var/www/identity_service/.env << 'EOF'
DATABASE_URL=mysql+pymysql://app_user:PasswordFuerte123@localhost/bar_identity_db
SECRET_KEY=$(openssl rand -hex 64)
FLASK_ENV=production
EOF
```

**4. Configurar MySQL para producción**
```sql
CREATE DATABASE bar_identity_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'PasswordFuerte123';
GRANT ALL PRIVILEGES ON bar_identity_db.* TO 'app_user'@'localhost';
FLUSH PRIVILEGES;
```

**5. Crear servicio systemd**
```bash
sudo cat > /etc/systemd/system/identity-service.service << 'EOF'
[Unit]
Description=Identity Service Flask API
After=network.target mysql.service

[Service]
Type=simple
User=identity_service
WorkingDirectory=/var/www/identity_service
EnvironmentFile=/var/www/identity_service/.env
ExecStart=/var/www/identity_service/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:5001 \
    --timeout 120 \
    --access-logfile /var/log/identity_service/access.log \
    --error-logfile /var/log/identity_service/error.log \
    app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo mkdir -p /var/log/identity_service
sudo systemctl daemon-reload
sudo systemctl enable identity-service
sudo systemctl start identity-service
```

**6. Configurar Nginx como reverse proxy**
```bash
sudo cat > /etc/nginx/sites-available/identity_service << 'EOF'
server {
    listen 80;
    server_name api.tudominio.com;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/auth/login {
        proxy_pass http://127.0.0.1:5001/api/auth/login;
        proxy_set_header Host $host;
    }

    location /api/auth/refresh {
        proxy_pass http://127.0.0.1:5001/api/auth/refresh;
        proxy_set_header Host $host;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/identity_service /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

**7. Configurar SSL (Let's Encrypt)**
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.tudominio.com
sudo systemctl reload nginx
```

---

### Opción 2: Docker + Docker Compose

**1. Crear Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5001
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "4", "app:app"]
```

**2. Crear docker-compose.yml**
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
    restart: unless-stopped

  identity_service:
    build: .
    ports:
      - "5001:5001"
    environment:
      DATABASE_URL: mysql+pymysql://root:root_password@identity_db:3306/bar_identity_db
      SECRET_KEY: ${SECRET_KEY}
    depends_on:
      - identity_db
    restart: unless-stopped

volumes:
  mysql_data:
```

**3. Desplegar**
```bash
# Crear red compartida (si hay otros servicios)
docker network create bar_network

# Ejecutar
docker-compose up -d

# Ver logs
docker-compose logs -f identity_service

# Escalar
docker-compose up -d --scale identity_service=3
```

**4. Configurar Nginx con Docker**
```yaml
# Añadir al docker-compose.yml
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - identity_service
    restart: unless-stopped
```

---

### Checklist de Producción

- [ ] **Variables de entorno**: SECRET_KEY generado con `openssl rand -hex 64`
- [ ] **Base de datos**: Usuario app dedicado, no root
- [ ] **HTTPS**: Siempre habilitado (SSL/TLS)
- [ ] **Gunicorn**: Mínimo 4 workers, timeout configurado
- [ ] **Logs**: Rotación configurada (logrotate)
- [ ] **Firewall**: Solo puertos 80/443 expuestos
- [ ] **Backups**: Automatizar backup de la base de datos
- [ ] **Health check**: Endpoint `/api/auth/login` disponible
- [ ] **Monitoreo**: Considerar agregar Prometheus metrics

---

## Licencia

Proprietary - Todos los derechos reservados.
