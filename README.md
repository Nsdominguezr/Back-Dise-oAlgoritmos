# API Gateway — Microservicio de Enrutamiento

## Propósito

Punto de entrada centralizado de la arquitectura de microservicios. Recibe todas las peticiones del frontend (Angular) y las reenvía a los microservicios backend correspondientes, funcionando como Reverse Proxy y BFF (Backend for Frontend).

---

## Arquitectura

```
┌─────────────┐        ┌─────────────────┐        ┌──────────────────┐
│   Angular   │ HTTPS  │   API Gateway   │  HTTP  │  Identity MS     │
│   Frontend  │───────▶│    (Flask)      │───────▶│   (Puerto 5001)  │
│  Puerto 4200│        │   Puerto 8000   │        └──────────────────┘
└─────────────┘        └────────┬────────┘
                               │ HTTP
                               ▼
                        ┌──────────────────┐
                        │  Catalog MS      │
                        │  (Puerto 5002)    │
                        └──────────────────┘
```

### Flujo de Peticiones

1. Frontend Angular envía peticiones a `/api/*`
2. Gateway recibe en puerto 8000 (HTTPS automático en desarrollo)
3. Lee configuración de enrutamiento y reenvía al microservicio destino
4. Microservicio procesa y devuelve respuesta
5. Gateway retorna respuesta al frontend

---

## Estructura del Proyecto

```
api_gateway/
├── app.py                    # Entry point — crea y arranca la app Flask
├── config.py                 # Configuración centralizada (puertos, URLs)
├── requirements.txt          # Dependencias Python
├── routes/
│   └── gateway_routes.py     # Blueprint con reglas de proxy/reenvío
└── venv/                     # Entorno virtual (excluido de git)
```

---

## Rutas Configuradas

| Ruta Entrada     | Microservicio Destino | Puerto |
|------------------|----------------------|--------|
| `/api/auth/*`    | Identity Service     | 5001   |
| `/api/sedes/*`   | Catalog Service      | 5002   |
| `/api/productos/*`| Catalog Service     | 5002   |

**Métodos HTTP:** GET, POST, PUT, DELETE, PATCH

El Gateway reenvía:
- Headers de petición (excepto `Host`)
- Body (JSON)
- Query parameters (`?id=1`)

---

## Instalación Local

### Requisitos

- Python 3.10+
- Git

### Pasos

```bash
# Clonar repositorio
git clone <repo-url>
cd api_gateway

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configuración opcional
cp .env.example .env  # Editar según necesidad

# Ejecutar
python app.py
```

Disponible en: **https://localhost:8000**

---

## Variables de Entorno

| Variable              | Default                              | Descripción                    |
|-----------------------|--------------------------------------|--------------------------------|
| `AUTH_SERVICE_URL`    | `http://127.0.0.1:5001/api/auth`     | URL del servicio de auth       |
| `CATALOG_SERVICE_URL` | `http://127.0.0.1:5002/api/sedes`    | URL base del catálogo          |

---

## Despliegue en Producción

### Docker + Nginx (Recomendado)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "app.py"]
```

```bash
docker build -t api-gateway:latest .
docker run -d --name api-gateway -p 8000:8000 \
  -e AUTH_SERVICE_URL=http://auth-service:5001/api/auth \
  -e CATALOG_SERVICE_URL=http://catalog-service:5002 \
  api-gateway:latest
```

### Nginx como Reverse Proxy (HTTPS)

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

## Troubleshooting

| Problema                  | Solución                                      |
|---------------------------|-----------------------------------------------|
| `Connection refused`      | Verificar que los microservicios estén activos |
| `CERTIFICATE_VERIFY_FAILED` | Usar `-k` con curl en desarrollo             |
| `502 Bad Gateway`         | Verificar URL del microservicio en `config.py` |
| Timeout en respuestas     | Aumentar `timeout=` en `gateway_routes.py`   |

---

## Dependencias

| Paquete         | Versión   | Propósito                        |
|-----------------|-----------|----------------------------------|
| Flask           | 3.0.2     | Framework web                    |
| Flask-CORS      | 4.0.0     | Soporte CORS                     |
| requests        | 2.31.0    | Reenvío de peticiones HTTP       |
| pyOpenSSL       | 26.0.0    | HTTPS automático (cert autofirmado)|
| python-dotenv   | 1.0.1     | Variables de entorno             |
