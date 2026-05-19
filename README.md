# Catalog Service - Microservicio de Gestión de Catálogo

Este repositorio contiene el **Microservicio de Catálogo**, un componente fundamental de la arquitectura de microservicios diseñada para el proyecto de Diseño de Algoritmos. Como Arquitecto de Software, este servicio ha sido estructurado siguiendo patrones de diseño modernos, garantizando escalabilidad, mantenibilidad y una separación clara de responsabilidades.

## 🏛️ Descripción Arquitectónica

El **Catalog Service** es responsable de la administración centralizada de las sedes (locales) y el inventario maestro de productos del sistema. 

### Patrón de Diseño
Se implementa una arquitectura basada en el patrón **MVC (Modelo-Vista-Controlador)** adaptada para APIs RESTful:
- **Modelo**: Definición de entidades con SQLAlchemy.
- **Controlador (Blueprints)**: Gestión de rutas y lógica de orquestación de peticiones.
- **DTO (Data Transfer Objects)**: Capa de serialización y validación de datos utilizando Marshmallow, desacoplando la base de datos de la respuesta de la API.

### Integración en el Ecosistema
Este servicio interactúa con el **Identity Service** para la validación de identidades mediante tokens JWT, compartiendo un secreto criptográfico para garantizar la integridad de las sesiones.

---

## 🛠️ Stack Tecnológico

- **Lenguaje:** Python 3.11+
- **Framework Web:** [Flask 3.0.3](https://flask.palletsprojects.com/)
- **ORM:** [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/)
- **Base de Datos:** MySQL 8.0+ (Conector PyMySQL)
- **Serialización/Validación:** [Marshmallow](https://marshmallow.readthedocs.io/)
- **Seguridad:** PyJWT (Autenticación basada en roles)

---

## 📂 Estructura del Proyecto

```text
catalog_service/
├── controllers/          # Lógica de manejo de peticiones (Blueprints)
│   ├── productos_controller.py
│   └── sedes_controller.py
├── models/               # Definición de modelos de base de datos
│   └── catalog_model.py
├── dto/                  # Data Transfer Objects y esquemas de validación
│   └── catalog_dto.py
├── utils/                # Middlewares y utilidades transversales
│   └── auth_middleware.py
├── config.py             # Configuración centralizada de la aplicación
├── app.py                # Punto de entrada y configuración del servidor
├── requirements.txt      # Dependencias del proyecto
└── README.md             # Documentación técnica
```

---

## 🚀 Configuración e Instalación

### Requisitos Previos
- Python 3.11 o superior instalado.
- Servidor MySQL activo con una base de datos llamada `bar_catalog_db`.

### Pasos de Instalación

1. **Clonar el repositorio:**
   ```bash
   git clone <url-del-repositorio>
   cd catalog_service
   ```

2. **Crear y activar un entorno virtual:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configuración de Variables de Entorno:**
   Actualmente, la configuración se encuentra en `config.py`. Se recomienda mover estas credenciales a un archivo `.env` en producción.
   - `SECRET_KEY`: Clave secreta para validación de tokens (Debe coincidir con Identity Service).
   - `SQLALCHEMY_DATABASE_URI`: Cadena de conexión a MySQL.

5. **Ejecutar el servicio:**
   ```bash
   python app.py
   ```
   El servicio estará disponible en `http://localhost:5002`.

---

## 📡 Documentación de la API

### Gestión de Sedes
| Método | Endpoint | Acceso | Descripción |
|---|---|---|---|
| `GET` | `/api/sedes` | Público | Lista todas las sedes registradas. |
| `POST` | `/api/sedes` | **Admin Global** | Registra una nueva sede en el sistema. |

### Gestión de Productos
| Método | Endpoint | Acceso | Descripción |
|---|---|---|---|
| `GET` | `/api/productos` | Público | Lista todos los productos activos. |
| `POST` | `/api/productos` | **Admin Global** | Crea un nuevo producto en el catálogo. |

> **Nota sobre Seguridad:** Los endpoints que requieren privilegios de **Admin Global** esperan un token JWT en el encabezado `Authorization` con el formato `Bearer <token>`.

---

## 📊 Modelo de Datos

### Sede
- `id`: Identificador único (Integer, PK).
- `nombre`: Nombre comercial de la sede (String 100).
- `direccion`: Ubicación física (String 150).
- `telefono`: Contacto telefónico (String 20).

### Producto
- `id`: Identificador único (Integer, PK).
- `nombre`: Nombre del producto (String 100).
- `precio`: Valor comercial (Numeric 10,2).
- `categoria`: Clasificación del producto (String 50).
- `activo`: Estado de disponibilidad (Boolean).

---

## 🛡️ Consideraciones del Arquitecto

1. **Escalabilidad**: El uso de Blueprints permite segmentar la lógica de negocio, facilitando el crecimiento del servicio sin comprometer la legibilidad.
2. **Seguridad**: Se implementa un decorador `@admin_global_required` para centralizar la validación de permisos, asegurando que solo personal autorizado pueda modificar el catálogo maestro.
3. **Mantenibilidad**: La separación entre modelos de base de datos y esquemas DTO permite cambiar la estructura interna de los datos sin afectar los contratos de la API consumidos por otros servicios o el frontend.

---
© 2024 - Diseñado por el Equipo de Arquitectura de Backend.
