# Servicio de Inventario (Inventory Microservice)

## Descripción del Proyecto

Este proyecto implementa el **Servicio de Inventario**, un microservicio fundamental dentro de una arquitectura de sistema distribuida. Su propósito principal es gestionar de manera centralizada la información y las operaciones relacionadas con el inventario de productos. Esto incluye la creación, lectura, actualización y eliminación (CRUD) de artículos, el seguimiento de existencias, y la gestión de disponibilidad.

Diseñado con un enfoque en la escalabilidad, la modularidad y la resiliencia, este microservicio se comunica con otros servicios de la arquitectura a través de una API RESTful, asegurando una separación de preocupaciones clara y facilitando el mantenimiento y la evolución del sistema en su conjunto.

## Arquitectura del Sistema

### Visión General
El Servicio de Inventario es un componente autónomo que encapsula toda la lógica de negocio y los datos relacionados con el inventario. Se integra con una base de datos MySQL dedicada y expone sus funcionalidades a través de una API RESTful.

```
+-------------------+     +---------------------+     +--------------------+
|  Otros Microservicios | <--> | Servicio de Inventario | <--> | Base de Datos MySQL |
|  (e.g., Pedidos, Catálogo) |     | (Flask Application)  |     | (Inventario)       |
+-------------------+     +---------------------+     +--------------------+
```

### Tecnologías Clave
- **Flask:** Micro-framework web para la construcción de la API RESTful.
- **Flask-SQLAlchemy:** ORM para la interacción con la base de datos relacional.
- **Marshmallow / Flask-Marshmallow:** Librería para la serialización/deserialización de objetos Python a/desde JSON, utilizada para DTOs y validación.
- **PyMySQL:** Conector nativo de MySQL para Python.
- **PyJWT / Bcrypt:** Para la codificación/decodificación de JSON Web Tokens y el hashing de contraseñas, asegurando la seguridad en la comunicación y autenticación (si aplica a nivel de microservicio).
- **python-dotenv:** Gestión de variables de entorno para una configuración segura y flexible.

### Patrones de Diseño
- **Microservicio:** Como componente independiente, se adhiere a los principios de los microservicios, enfocándose en una única responsabilidad.
- **Arquitectura en Capas (MVC-like):** La estructura del proyecto (`controllers`, `dto`, `models`) refleja una separación de preocupaciones similar al patrón MVC, donde los controladores manejan las peticiones, los DTOs gestionan la transferencia de datos, y los modelos interactúan con la base de datos.
- **API RESTful:** La comunicación se realiza mediante un conjunto de principios y restricciones para la construcción de servicios web.

## Características Principales

*   **Gestión de Artículos (CRUD):** Creación, consulta, actualización y eliminación de productos en el inventario.
*   **Gestión de Existencias:** Seguimiento de la cantidad disponible de cada artículo.
*   **Actualización de Inventario:** Operaciones para añadir o sustraer unidades de productos.
*   **Consulta de Disponibilidad:** Verificación rápida de la disponibilidad de un producto.
*   **Seguridad:** Implementación de JWT para la autenticación y autorización de las peticiones a la API.

## Tecnologías Utilizadas

*   **Lenguaje:** Python 3.x
*   **Framework Web:** Flask (3.0.3)
*   **ORM:** Flask-SQLAlchemy (3.1.1)
*   **Conector DB:** PyMySQL (1.1.0)
*   **Serialización/DTOs:** Flask-Marshmallow (1.2.1), Marshmallow (3.21.1), Marshmallow-SQLAlchemy (1.0.0)
*   **Seguridad:** Bcrypt (4.1.2), PyJWT (2.8.0)
*   **Variables de Entorno:** python-dotenv (1.0.1)
*   **Peticiones HTTP:** requests (2.31.0)
*   **Base de Datos:** MySQL

## Estructura del Proyecto

```
.
├── app.py                  # Punto de entrada principal de la aplicación Flask.
├── config.py               # Configuración de la aplicación (base de datos, secretos, etc.).
├── controllers/            # Lógica de manejo de peticiones HTTP y enrutamiento (blueprints).
│   └── inventory_controller.py
├── dto/                    # Objetos de Transferencia de Datos (DTOs) y esquemas de Marshmallow.
│   └── inventory_dto.py
├── models/                 # Definiciones de modelos de base de datos con SQLAlchemy.
│   └── inventory_model.py
├── utils/                  # Módulos con funciones de utilidad compartidas.
├── requirements.txt        # Dependencias del proyecto.
├── README.md               # Este archivo.
└── venv/                   # Entorno virtual de Python.
```

## Configuración del Entorno

Sigue estos pasos para configurar y ejecutar el proyecto localmente:

### Pre-requisitos
*   **Python 3.x:** Asegúrate de tener Python instalado.
*   **pip:** Gestor de paquetes de Python.
*   **MySQL:** Un servidor de base de datos MySQL en ejecución.

### 1. Clonar el Repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd inventory_service
```

### 2. Crear y Activar el Entorno Virtual

Es recomendable utilizar un entorno virtual para aislar las dependencias del proyecto.

```bash
python3 -m venv venv
source venv/bin/activate  # En Linux/macOS
# venv\Scripts\activate   # En Windows
```

### 3. Instalar Dependencias

Instala todas las librerías necesarias utilizando `pip`:

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto (al mismo nivel que `app.py`). Este archivo contendrá las variables de entorno sensibles y de configuración.

Ejemplo de `.env`:

```dotenv
# Configuración de la Base de Datos
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=inventory_db

# Secreto de la aplicación Flask (genera uno fuerte y único)
SECRET_KEY='your_super_secret_key'

# Configuración JWT (para autenticación)
JWT_SECRET_KEY='your_jwt_secret_key'
```

Asegúrate de reemplazar los valores de ejemplo con tu propia configuración.

## Configuración de la Base de Datos

### 1. Crear la Base de Datos

Conéctate a tu servidor MySQL (por ejemplo, usando la línea de comandos de MySQL o una herramienta como MySQL Workbench) y crea la base de datos:

```sql
CREATE DATABASE inventory_db;
```

### 2. Configuración en `.env`

Asegúrate de que el nombre de la base de datos y las credenciales en tu archivo `.env` coincidan con tu configuración de MySQL.

### 3. Ejecutar Migraciones (si aplica)

Si hay scripts de migración de base de datos (por ejemplo, con Flask-Migrate o Alembic), ejecútalos para crear las tablas necesarias. (Actualmente no se observan herramientas de migración, se asume creación de tablas por SQLAlchemy al iniciar la app o una migración manual inicial).

```bash
# Ejemplo, si se usa Flask-Migrate
# flask db init
# flask db migrate -m "Initial migration"
# flask db upgrade
```
**Nota:** Si las tablas no se crean automáticamente, es posible que necesites ejecutar un script para inicializar el esquema de la base de datos o que se creen al primer acceso.

## Ejecución del Servicio

Para iniciar el microservicio, ejecuta el siguiente comando desde la raíz del proyecto con el entorno virtual activado:

```bash
python app.py
```

El servicio se ejecutará en `http://0.0.0.0:5003` (o el puerto configurado en `app.py`).

## Endpoints de la API

A continuación, se describen los endpoints principales que expone el Servicio de Inventario. (Nota: Para detalles específicos de los payloads y respuestas, consulte la documentación de la API o el código fuente en `controllers/inventory_controller.py`).

*   **`GET /api/inventory`**: Obtener todos los artículos del inventario.
*   **`POST /api/inventory`**: Crear un nuevo artículo en el inventario.
*   **`GET /api/inventory/<id>`**: Obtener un artículo específico por su ID.
*   **`PUT /api/inventory/<id>`**: Actualizar un artículo existente.
*   **`DELETE /api/inventory/<id>`**: Eliminar un artículo del inventario.
*   **`PUT /api/inventory/<id>/add`**: Añadir unidades a un artículo existente.
*   **`PUT /api/inventory/<id>/remove`**: Sustraer unidades de un artículo existente.

## Pruebas

Para ejecutar las pruebas del proyecto (si existen), utiliza el siguiente comando:

```bash
# Ejemplo: si se usa pytest
# pytest
```
**Nota:** Se recomienda implementar un conjunto de pruebas unitarias y de integración para asegurar el correcto funcionamiento del microservicio.

## Consideraciones de Seguridad

*   **Variables de Entorno:** Todas las configuraciones sensibles (credenciales de base de datos, claves secretas) deben almacenarse en el archivo `.env` y no ser directamente versionadas.
*   **JWT:** El uso de JSON Web Tokens ayuda a proteger los endpoints de la API, asegurando que solo las peticiones autenticadas y autorizadas puedan acceder a los recursos.
*   **Validación de Entrada:** Implementar validación robusta para todas las entradas de la API para prevenir inyecciones y otros ataques comunes.

## Contribución

¡Las contribuciones son bienvenidas! Si deseas contribuir a este proyecto, por favor sigue estos pasos:

1.  Haz un "fork" del repositorio.
2.  Crea una nueva rama para tu característica (`git checkout -b feature/AmazingFeature`).
3.  Realiza tus cambios y asegúrate de que pasen las pruebas.
4.  Haz un "commit" de tus cambios (`git commit -m 'Add some AmazingFeature'`).
5.  Sube la rama (`git push origin feature/AmazingFeature`).
6.  Abre un "Pull Request".

## Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles. (Si aplica, crear archivo `LICENSE` si no existe).
