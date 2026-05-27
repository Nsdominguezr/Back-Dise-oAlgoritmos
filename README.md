# Orders Service — Microservicio de Gestión de Pedidos

## Resumen Arquitectónico

El **Orders Service** es responsable de la gestión operativa del flujo de pedidos en el sistema. Administra mesas, pedidos, items, caja, pagos y utiliza un **algoritmo de optimización de cola** basado en el patrón de la **Mochila (Knapsack)** con programación dinámica.

### Responsabilidades Core

- Gestión de mesas por sede (alta, consulta, eliminación lógica)
- Creación y edición de pedidos
- Agregar items a pedidos (con validación de stock via Inventory Service)
- Gestión de caja y procesamiento de pagos
- Historial y trazabilidad de transacciones
- Reportes financieros consolidados

### Integraciones Externas

| Servicio              | Propósito                                    | Puerto |
|-----------------------|----------------------------------------------|--------|
| Inventory Service     | Validación de stock y descuento post-venta   | 5003   |
| Catalog Service       | Consulta de nombres de sede para reportes   | 5002   |
| Identity Service      | Autenticación y autorización (middleware)    | 5001   |

---

## Arquitectura

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Orders Service                                │
│                                                                       │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────────┐           │
│  │ Controllers  │───▶│   Models     │───▶│    MySQL      │           │
│  │ (Blueprints) │    │(SQLAlchemy)  │    │ bar_orders_db │           │
│  └──────┬───────┘    └──────────────┘    └───────────────┘           │
│         │                                                          │
│         ▼                                                          │
│  ┌──────────────┐    ┌──────────────┐                               │
│  │     DTO     │◀───│  Response    │                               │
│  │(Marshmallow)│    │   (JSON)     │                               │
│  └──────────────┘    └──────────────┘                               │
│                                                                       │
│  🔗 Inventory Service ──▶ Validación stock                          │
│  🔗 Catalog Service  ──▶ Nombres de sede                             │
└──────────────────────────────────────────────────────────────────────┘
```

### Algoritmo de Optimización (Mochila DP)

El servicio implementa el algoritmo de la **mochila con programación dinámica** para optimizar el procesamiento de pedidos en cola:

```
resolver_mochila_pedidos(pedidos, capacidad)
├── Ordena pedidos por ratio beneficio/volumen
├── Tabla DP[n+1][capacidad_max+1]
├── Selecciona combinación óptima de pedidos
└── Retorna: pedidos_seleccionados, items_total, beneficio_total
```

---

## Stack Tecnológico

| Componente        | Tecnología                 | Propósito                        |
|-------------------|----------------------------|----------------------------------|
| Runtime          | Python 3.x                 | Lenguaje de implementación       |
| Framework        | Flask 3.0.3                | API REST                         |
| ORM              | Flask-SQLAlchemy 3.1.1      | Interacción con base de datos    |
| Conector DB      | PyMySQL 1.1.0              | Conexión nativa MySQL            |
| Serialización    | Flask-Marshmallow 1.2.1    | DTOs y validación                |
| Seguridad        | Bcrypt 4.1.2, PyJWT 2.8.0  | Hashing y autenticación JWT      |
| Comunicación     | requests 2.31.0            | HTTP sincrónico entre servicios  |
| Variables ENV    | python-dotenv 1.0.1         | Configuración flexible           |

---

## Estructura del Proyecto

```
orders_service/
├── app.py                       # Entry point — servidor Flask (puerto 5004)
├── config.py                    # Configuración centralizada
├── requirements.txt             # Dependencias Python
├── controllers/
│   └── orders_controller.py     # Blueprints — lógica de negocio + algoritmo mochila
├── models/
│   └── orders_model.py          # Modelos SQLAlchemy (Mesa, Pedido, DetallePedido, Pago)
├── utils/
│   └── auth_middleware.py       # Middlewares de autenticación
└── venv/                       # Entorno virtual (excluido de git)
```

---

## Modelo de Datos

### Mesa

| Campo         | Tipo                      | Descripción                        |
|---------------|---------------------------|------------------------------------|
| id            | Integer (PK)              | Identificador único                |
| sede_id       | Integer                   | Sede a la que pertenece           |
| numero_mesa   | String(10)                | Identificador visual              |
| estado        | Enum('LIBRE','OCUPADA')   | Estado actual                      |
| activo        | Boolean                   | Soft delete (True = activa)       |

### Pedido

| Campo          | Tipo                             | Descripción                    |
|----------------|----------------------------------|--------------------------------|
| id             | Integer (PK)                     | Identificador único            |
| mesa_id        | Integer (FK → mesas.id)          | Mesa asociada                  |
| usuario_id     | Integer                          | Mesero que creó el pedido      |
| estado         | Enum('ABIERTO','PENDIENTE_PAGO','PAGADO') | Estado del pedido |
| total          | Numeric(10,2)                    | Monto total acumulado          |
| fecha_creacion | DateTime                         | Timestamp de creación          |

### DetallePedido

| Campo           | Tipo            | Descripción                      |
|-----------------|-----------------|----------------------------------|
| id              | Integer (PK)    | Identificador único              |
| pedido_id       | Integer (FK)    | Pedido padre                     |
| producto_id     | Integer         | Producto del catálogo            |
| cantidad        | Integer         | Cantidad ordenada                |
| precio_unitario | Numeric(10,2)   | Precio al momento del pedido     |

### Pago

| Campo         | Tipo                            | Descripción                |
|---------------|----------------------------------|----------------------------|
| id            | Integer (PK)                     | Identificador único        |
| pedido_id     | Integer (FK → pedidos.id)        | Pedido asociado            |
| medio_pago    | Enum('EFECTIVO','TC','TD')       | Método de pago             |
| monto_pagado  | Numeric(10,2)                    | Monto cobrado              |
| fecha_pago    | DateTime                         | Timestamp del pago         |

---

## API Endpoints

### Gestión de Mesas

| Método | Endpoint                    | Auth              | Descripción                        |
|--------|-----------------------------|-------------------|------------------------------------|
| GET    | `/api/pedidos/mesas/<sede_id>` | Token          | Lista mesas activas de una sede    |
| POST   | `/api/pedidos/mesas`        | Admin Local/Global| Crear nueva mesa                   |
| PATCH  | `/api/pedidos/mesas/<mesa_id>` | Admin Local/Global| Eliminar mesa (soft delete)      |

### Gestión de Pedidos

| Método | Endpoint                              | Auth  | Descripción                          |
|--------|---------------------------------------|-------|--------------------------------------|
| POST   | `/api/pedidos/abrir`                 | Token | Abrir pedido para una mesa           |
| POST   | `/api/pedidos/<pedido_id>/items`      | Token | Agregar item al pedido              |
| PATCH  | `/api/pedidos/<pedido_id>/pasar-a-caja` | Token | Enviar pedido a caja (bloquear edición) |
| POST   | `/api/pedidos/<pedido_id>/checkout`   | Token | Procesar pago y cerrar pedido        |

### Caja y Reportes

| Método | Endpoint                                   | Auth              | Descripción                         |
|--------|-------------------------------------------|-------------------|-------------------------------------|
| GET    | `/api/pedidos/caja/pendientes/<sede_id>` | Token             | Pedidos pendientes de pago          |
| GET    | `/api/pedidos/pagos/historial/<sede_id>` | Token             | Historial de pagos por sede         |
| GET    | `/api/pedidos/reportes/financiero`       | Admin Global      | CSV con resumen financiero consolidado |
| POST   | `/api/pedidos/optimizar-cola`            | Admin Local/Global| Optimizar cola con algoritmo mochila |

---

## Algoritmo de la Mochila — Optimización de Cola

### Endpoint: `POST /api/pedidos/optimizar-cola`

**Request:**
```json
{
  "sede_id": 1,
  "capacidad_items": 20
}
```

**Response:**
```json
{
  "sede_id": 1,
  "capacidad_items": 20,
  "pedidos_seleccionados": [3, 7, 1],
  "items_total": 18,
  "beneficio_total": 245.50,
  "pedidos_omitidos": [5, 2],
  "total_pedidos_pendientes": 5
}
```

### Lógica del Algoritmo

1. **Ordenamiento**: Pedidos se ordenan por ratio `beneficio/cantidad_items`
2. **Programación Dinámica**: Tabla DP para encontrar combinación óptima
3. **Resultado**: Maximiza revenue respetando límite de capacidad

---

## Integración con Inventory Service

El servicio se comunica sincrónicamente con Inventory Service para:

### Validación de Stock (al agregar item)
```
POST /api/inventory/sede/{sede_id} → Verifica stock disponible
```

### Descuento de Stock (post-checkout)
```
POST /api/inventory/descontar-venta → Descuenta items vendidos
```

---

## Instalación Local

### Requisitos

- Python 3.x
- MySQL 8.0+ (base de datos: `bar_orders_db`)
- Inventory Service activo (puerto 5003)
- Catalog Service activo (puerto 5002)

### Pasos

```bash
# Clonar repositorio
git clone <URL_DEL_REPOSITORIO>
cd orders_service

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Crear base de datos
mysql -u root -p -e "CREATE DATABASE bar_orders_db;"

# Configurar variables de entorno
# Editar config.py o crear .env con las URLs de servicios

# Ejecutar servicio
python app.py
```

Disponible en: `http://localhost:5004`

---

## Despliegue en Producción

### Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5004
CMD ["python", "app.py"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  orders_db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root_password
      MYSQL_DATABASE: bar_orders_db
    volumes:
      - orders_data:/var/lib/mysql

  orders_service:
    build: .
    ports:
      - "5004:5004"
    environment:
      MYSQL_HOST: orders_db
      MYSQL_USER: root
      MYSQL_PASSWORD: root_password
      MYSQL_DB: bar_orders_db
      INVENTORY_SERVICE_URL: http://inventory_service:5003/api/inventario
      CATALOG_SERVICE_URL: http://catalog_service:5002/api
    depends_on:
      - orders_db

volumes:
  orders_data:
```

---

## Middleware de Autenticación

| Decorador                    | Roles Permitidos              | Uso                        |
|------------------------------|-------------------------------|----------------------------|
| `@token_required`            | Todos los roles autenticados  | Lectura general            |
| `@admin_local_or_global_required` | Admin Local, Admin Global | Gestión de mesas           |
| `@admin_global_required`     | Admin Global                 | Reportes financieros       |

---

## Licencia

MIT License
