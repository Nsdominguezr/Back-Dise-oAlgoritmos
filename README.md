# Catalog Service — Microservicio de Gestión de Catálogo

## Resumen Arquitectónico

El **Catalog Service** es responsable de la administración centralizada del catálogo maestro del sistema, gestionando entidades de alto nivel como **Sedes** y **Productos**. Este servicio opera como la fuente autoritativa de información de referencia para el resto de la arquitectura de microservicios.

### Patrones de Diseño

- **MVC Adaptado a REST**: Modelos SQLAlchemy (datos), Blueprints (controladores), Marshmallow DTOs (serialización)
- **Servicio Stateful**: Gestiona persistencia en MySQL con transacciones ACID
- **Autenticación Basada en Tokens**: Integración con Identity Service mediante JWT compartido

---

## Stack Tecnológico

| Componente       | Tecnología                    | Propósito                              |
|------------------|-------------------------------|----------------------------------------|
| Runtime         | Python 3.11+                  | Lenguaje de implementación             |
| Framework       | Flask 3.0.3                   | API REST                               |
| ORM             | Flask-SQLAlchemy              | Mapeo objeto-relacional                |
| Base de Datos   | MySQL 8.0+                    | Persistencia relacional                 |
| Serialización   | Marshmallow + Flask-Marshmallow | DTOs y validación de esquemas       |
| Autenticación   | PyJWT                         | Tokens JWT (secret compartido)         |

---

## Arquitectura de Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                     Catalog Service                          │
│                                                              │
│  ┌────────────┐    ┌────────────┐    ┌───────────────┐    │
│  │ Controllers│───▶│   Models   │───▶│     MySQL      │    │
│  │ (Blueprints)│    │(SQLAlchemy)│    │ bar_catalog_db │    │
│  └──────┬─────┘    └────────────┘    └───────────────┘    │
│         │                                                  │
│         ▼                                                  │
│  ┌────────────┐    ┌────────────┐                         │
│  │    DTO     │◀───│  Response  │                         │
│  │(Marshmallow│    │   (JSON)    │                         │
│  └────────────┘    └────────────┘                         │
│                                                              │
│  🔗 Identity Service (JWT Validation)                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Estructura del Proyecto

```
catalog_service/
├── app.py                     # Entry point y configuración del servidor
├── config.py                  # Configuración centralizada
├── requirements.txt           # Dependencias Python
├── controllers/               # Lógica de manejo de peticiones (Blueprints)
│   ├── productos_controller.py
│   └── sedes_controller.py
├── models/                    # Definición de modelos de base de datos
│   └── catalog_model.py
├── dto/                       # Data Transfer Objects y esquemas de validación
│   └── catalog_dto.py
└── utils/                     # Middlewares y utilidades transversales
    └── auth_middleware.py
```

---

## Modelo de Datos

### Sede

| Campo     | Tipo         | Descripción                        |
|-----------|--------------|-------------------------------------|
| id        | Integer (PK) | Identificador único                 |
| nombre    | String(100)  | Nombre comercial de la sede         |
| direccion | String(150)  | Ubicación física                    |
| telefono  | String(20)   | Contacto telefónico                 |

### Producto

| Campo     | Tipo            | Descripción                      |
|-----------|-----------------|----------------------------------|
| id        | Integer (PK)    | Identificador único              |
| nombre    | String(100)     | Nombre del producto              |
| precio    | Numeric(10,2)   | Valor comercial                  |
| categoria | String(50)      | Clasificación del producto       |
| activo    | Boolean         | Estado de disponibilidad         |

---

## API Endpoints

### Gestión de Sedes

| Método | Endpoint      | Acceso         | Descripción                      |
|--------|---------------|----------------|----------------------------------|
| GET    | `/api/sedes`  | Público        | Lista todas las sedes registradas|
| POST   | `/api/sedes`  | Admin Global   | Registra una nueva sede          |

### Gestión de Productos

| Método | Endpoint         | Acceso         | Descripción                    |
|--------|------------------|----------------|--------------------------------|
| GET    | `/api/productos` | Público       | Lista todos los productos activos|
| POST   | `/api/productos` | Admin Global  | Crea un nuevo producto         |

> **Nota de Seguridad**: Los endpoints protegidos esperan `Authorization: Bearer <token>` con rol Admin Global.

---

## Instalación Local

### Requisitos Previos

- Python 3.11+
- MySQL 8.0+ con base de datos `bar_catalog_db`

### Pasos

```bash
# Clonar repositorio
git clone <url-del-repositorio>
cd catalog_service

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
# Editar config.py o crear .env con:
# SECRET_KEY (debe coincidir con Identity Service)
# SQLALCHEMY_DATABASE_URI

# Ejecutar servicio
python app.py
```

Disponible en: `http://localhost:5002`

---

## Consideraciones de Diseño

| Aspecto          | Decisión Arquitectónica                               |
|------------------|------------------------------------------------------|
| Escalabilidad    | Blueprints permiten segmentar lógica por dominio    |
| Seguridad        | Decorador `@admin_global_required` centraliza Auth |
| Mantenibilidad   | Separación DTO/Modelos permite evolución independiente|
| Integración      | Secret JWT compartido con Identity Service          |

---

## Dependencias

| Paquete              | Versión   | Propósito                     |
|----------------------|-----------|-------------------------------|
| Flask                | 3.0.3     | Framework web                 |
| Flask-SQLAlchemy     | 3.1.x     | ORM                           |
| Flask-Marshmallow    | 1.2.x     | Serialización DTOs           |
| PyMySQL              | 1.1.x     | Conector MySQL               |
| PyJWT                | 2.8.x     | Autenticación JWT            |
| python-dotenv        | 1.0.x     | Variables de entorno          |

---

*© 2024 — Diseñado por el Equipo de Arquitectura de Backend.*
