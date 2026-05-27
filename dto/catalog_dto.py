"""Módulo de DTOs (Data Transfer Objects) del catálogo.

Contiene los esquemas de serialización para Sede y Producto.
"""

from flask_marshmallow import Marshmallow
from models.catalog_model import Sede, Producto

ma = Marshmallow()


class SedeDTO(ma.SQLAlchemyAutoSchema):
    """Esquema de serialización para el modelo Sede."""

    class Meta:
        model = Sede
        fields = ("id", "nombre", "direccion", "telefono", "activo")  # <-- AÑADIDO 'activo'.


class ProductoDTO(ma.SQLAlchemyAutoSchema):
    """Esquema de serialización para el modelo Producto."""

    class Meta:
        model = Producto
        fields = ("id", "nombre", "precio", "categoria", "activo")


# Instancias para usar en los controladores.
sede_dto = SedeDTO()
sedes_dto = SedeDTO(many=True)
producto_dto = ProductoDTO()
productos_dto = ProductoDTO(many=True)