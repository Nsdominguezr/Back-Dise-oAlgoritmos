# API Gateway

Reverse proxy que recibe peticiones del frontend (Angular) y las reenvía a los microservicios backend.

## Tecnologías

- **Flask 3.0.2** — Framework web
- **Flask-CORS 4.0.0** — Soporte CORS
- **requests 2.31.0** — Reenvío de peticiones HTTP
- **pyOpenSSL 26.0.0** — HTTPS automático
- **python-dotenv 1.0.1** — Variables de entorno

## Rutas configuradas

| Ruta | Servicio |
|------|----------|
| `/api/auth` | `http://127.0.0.1:5001/api/auth` |
| `/api/sedes` | `http://127.0.0.1:5002/api/sedes` |
| `/api/productos` | `http://127.0.0.1:5002/api/productos` |

Soporta GET, POST, PUT, DELETE, PATCH. Pasa headers, body y query params intactos.

## Instalación

```bash
git clone <repo-url>
cd api_gateway
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Uso

```bash
python app.py
```

El gateway inicia en **puerto 8000** con HTTPS habilitado automáticamente.

## Variables de entorno (opcionales)

```bash
export AUTH_SERVICE_URL=http://127.0.0.1:5001/api/auth
export CATALOG_SERVICE_URL=http://127.0.0.1:5002/api/sedes
```