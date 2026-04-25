# API Gateway

Reverse proxy centralizado que recibe todas las peticiones del frontend (Angular) y las reenvía a los microservicios backend correspondientes.

---

## Arquitectura

```
┌─────────────┐     HTTPS      ┌───────────────┐     HTTP      ┌──────────────┐
│   Angular   │ ────────────►  │  API Gateway  │ ───────────►  │  Auth MS     │
│   Frontend  │                │   (Flask)    │               │  (Puerto 5001)│
│  Puerto 4200│                │  Puerto 8000  │               └──────────────┘
└─────────────┘                └───────────────┘
                                      │
                                      │ HTTP
                                      ▼
                               ┌──────────────┐
                               │ Catalog MS   │
                               │(Puertos 5002)│
                               └──────────────┘
```

### Flujo de peticiones

1. El frontend Angular envía peticiones a `/api/*`
2. El Gateway recibe la petición en puerto 8000 (HTTPS automático)
3. Lee la configuración de enrutamiento y reenvía al microservicio correspondiente
4. El microservicio procesa y devuelve la respuesta
5. El Gateway retorna la respuesta al frontend

---

## Estructura del Proyecto

```
api_gateway/
├── app.py                 # Punto de entrada. Crea la app Flask y arranca el servidor
├── config.py              # Configuración centralizada: puertos, URLs de microservicios
├── requirements.txt       # Dependencias Python
├── routes/
│   └── gateway_routes.py  # Blueprint con las reglas de proxy/reenvío
└── venv/                  # Entorno virtual Python (no incluir en git)
```

---

## Rutas configuradas

| Ruta entrada | Microservicio destino | Puerto |
|--------------|------------------------|--------|
| `/api/auth/*` | Auth Service | 5001 |
| `/api/sedes/*` | Catalog Service | 5002 |
| `/api/productos/*` | Catalog Service | 5002 |

**Métodos HTTP soportados:** GET, POST, PUT, DELETE, PATCH

El Gateway reenvía:
- Headers de la petición (excepto `Host`)
- Body (JSON)
- Query parameters (`?id=1`)

---

## Instalación local (Desarrollo)

### Prerrequisitos

- Python 3.10+
- Git

### Pasos

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd api_gateway

# 2. Crear entorno virtual
python3 -m venv venv

# 3. Activar entorno virtual
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. (Opcional) Configurar URLs de microservicios
cp .env.example .env  #Editar segun necesidad

# 6. Ejecutar
python app.py
```

El Gateway estará disponible en: **https://localhost:8000**

---

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `AUTH_SERVICE_URL` | `http://127.0.0.1:5001/api/auth` | URL del microservicio de autenticación |
| `CATALOG_SERVICE_URL` | `http://127.0.0.1:5002/api/sedes` | URL base del microservicio de catálogo |

---

## Despliegue en Producción

### Opción 1: Docker + Nginx (Recomendado)

#### 1. Crear Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "app.py"]
```

#### 2. Construir imagen

```bash
docker build -t api-gateway:latest .
```

#### 3. Ejecutar contenedor

```bash
docker run -d \
  --name api-gateway \
  -p 8000:8000 \
  -e AUTH_SERVICE_URL=http://auth-service:5001/api/auth \
  -e CATALOG_SERVICE_URL=http://catalog-service:5002 \
  api-gateway:latest
```

#### 4. Configurar Nginx como reverse proxy (HTTPS)

```nginx
server {
    listen 443 ssl;
    server_name api.tu-dominio.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name api.tu-dominio.com;
    return 301 https://$server_name$request_uri;
}
```

#### 5. Aplicar configuración Nginx

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

### Opción 2: Docker Compose (Multi-servicio)

```yaml
version: '3.8'

services:
  api-gateway:
    build: .
    ports:
      - "8000:8000"
    environment:
      - AUTH_SERVICE_URL=http://auth-service:5001/api/auth
      - CATALOG_SERVICE_URL=http://catalog-service:5002
    depends_on:
      - auth-service
      - catalog-service

  auth-service:
    image: auth-service:latest
    ports:
      - "5001:5001"

  catalog-service:
    image: catalog-service:latest
    ports:
      - "5002:5002"

  nginx:
    image: nginx:latest
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api-gateway
```

Ejecutar: `docker-compose up -d`

---

### Opción 3: Servicio sistémico (Systemd)

Crear archivo `/etc/systemd/system/api-gateway.service`:

```ini
[Unit]
Description=API Gateway Flask
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/api-gateway
Environment="AUTH_SERVICE_URL=http://auth-service:5001/api/auth"
Environment="CATALOG_SERVICE_URL=http://catalog-service:5002"
ExecStart=/opt/api-gateway/venv/bin/python /opt/api-gateway/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable api-gateway
sudo systemctl start api-gateway
```

---

## Certificado SSL

El Gateway genera automáticamente un certificado autofirmado en desarrollo. Para producción usar certificados de Let's Encrypt:

```bash
sudo certbot --nginx -d api.tu-dominio.com
```

---

## Verificación

```bash
# Health check
curl https://localhost:8000/api/auth/health

# Probar enrutamiento
curl -X GET https://localhost:8000/api/sedes
```

---

## Solución de problemas

| Problema | Solución |
|----------|----------|
| `Connection refused` | Verificar que los microservicios estén corriendo |
| `CERTIFICATE_VERIFY_FAILED` | En desarrollo, usar `-k` con curl o importar el cert |
| `502 Bad Gateway` | Verificar que la URL del microservicio en `config.py` sea correcta |
| Timeout en respuestas | Aumentar `timeout=` en `gateway_routes.py` línea 25 |

---

## Dependencias

- **Flask 3.0.2** — Framework web
- **Flask-CORS 4.0.0** — Soporte CORS
- **requests 2.31.0** — Reenvío de peticiones HTTP
- **pyOpenSSL 26.0.0** — HTTPS automático (certificado autofirmado)
- **python-dotenv 1.0.1** — Variables de entorno