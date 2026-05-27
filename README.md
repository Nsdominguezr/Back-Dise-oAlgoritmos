# Inventory Service — Microservicio de Gestión de Inventario

## Resumen

Microservicio autónomo responsable de la gestión centralizada del inventario de productos. Maneja operaciones de CRUD para artículos, seguimiento de existencias, y gestión de disponibilidad. Se comunica con otros servicios mediante API RESTful.

---

## Arquitectura

```
┌─────────────────────┐     ┌─────────────────────────┐     ┌────────────────┐
│ Otros Microservicios│◀───▶│   Inventory Service      │◀───▶│  MySQL         │
│ (Orders, Catalog)   │     │      (Flask)            │     │ inventory_db   │
└─────────────────────┘     └─────────────────────────┘     └────────────────┘
```

### Patrones de Diseño

- **Microservicio Stateful**: Una única responsabilidad, base de datos dedicada
- **Arquitectura en Capas (MVC-like)**: Controllers, DTOs, Models
- **API RESTful**: Comunicación estructurada mediante principios REST

---

## Stack Tecnológico

| Componente        | Tecnología                 | Propósito                        |
|-------------------|----------------------------|----------------------------------|
| Runtime          | Python 3.x                 | Lenguaje de implementación       |
| Framework        | Flask 3.0.3                | API REST                         |
| ORM              | Flask-SQLAlchemy 3.1.1      | Interacción con base de datos    |
| Conector DB      | PyMySQL 1.1.0              | Conexión nativa MySQL            |
| Serialización    | Flask-Marshmallow 1.2.1    | DTOs y validación de esquemas    |
| Seguridad        | Bcrypt 4.1.2, PyJWT 2.8.0  | Hashing y autenticación JWT      |
| Variables ENV    | python-dotenv 1.0.1         | Configuración flexible           |

---

## Estructura del Proyecto

```
inventory_service/
├── app.py                      # Entry point — aplicación Flask
├── config.py                   # Configuración (DB, secretos)
├── controllers/                # Blueprints — lógica de routing
│   └── inventory_controller.py
├── dto/                        # Esquemas Marshmallow — serialización
│   └── inventory_dto.py
├── models/                     # Modelos SQLAlchemy
│   └── inventory_model.py
├── utils/                      # Utilidades compartidas
├── requirements.txt            # Dependencias Python
└── venv/                       # Entorno virtual (excluido de git)
```

---

## Endpoints de la API

| Método | Endpoint                        | Descripción                         |
|--------|----------------------------------|-------------------------------------|
| GET    | `/api/inventory`                | Obtener todos los artículos         |
| POST   | `/api/inventory`                | Crear nuevo artículo                |
| GET    | `/api/inventory/<id>`           | Obtener artículo por ID             |
| PUT    | `/api/inventory/<id>`           | Actualizar artículo existente       |
| DELETE | `/api/inventory/<id>`           | Eliminar artículo                   |
| PUT    | `/api/inventory/<id>/add`       | Añadir unidades                     |
| PUT    | `/api/inventory/<id>/remove`    | Sustraer unidades                   |

---

## Instalación Local

### Requisitos

- Python 3.x
- MySQL (servidor activo)
- pip

### Pasos

```bash
# Clonar repositorio
git clone <URL_DEL_REPOSITORIO>
cd inventory_service

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Crear base de datos
mysql -u root -p -e "CREATE DATABASE inventory_db;"

# Configurar variables de entorno (.env)
cp .env.example .env  # Editar con credenciales

# Ejecutar servicio
python app.py
```

Disponible en: `http://0.0.0.0:5003`

---

## Configuración de Variables de Entorno

```dotenv
# Base de Datos
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=inventory_db

# Secretos
SECRET_KEY='your_super_secret_key'
JWT_SECRET_KEY='your_jwt_secret_key'
```

---

## Consideraciones de Seguridad

| Aspecto               | Práctica Recomendada                           |
|-----------------------|-----------------------------------------------|
| Credenciales          | Almacenar en `.env`, nunca en código          |
| JWT                   | Proteger endpoints sensibles                   |
| Validación de Entrada | Validar todos los inputs para prevenir inyecciones |
| Secrets               | Usar valores fuertes y únicos por entorno      |

---

## Despliegue en Producción

### Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5003
CMD ["python", "app.py"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  inventory_db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root_password
      MYSQL_DATABASE: inventory_db
    volumes:
      - inventory_data:/var/lib/mysql

  inventory_service:
    build: .
    ports:
      - "5003:5003"
    environment:
      MYSQL_HOST: inventory_db
      MYSQL_USER: root
      MYSQL_PASSWORD: root_password
      MYSQL_DB: inventory_db
    depends_on:
      - inventory_db

volumes:
  inventory_data:
```

---

## Licencia

MIT License
