from flask_marshmallow import Marshmallow
from models.catalog_model import Sede, Producto

ma = Marshmallow()

class SedeDTO(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Sede
        fields = ("id", "nombre", "direccion", "telefono")

class ProductoDTO(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Producto
        fields = ("id", "nombre", "precio", "categoria", "activo")

sede_dto = SedeDTO()
sedes_dto = SedeDTO(many=True)
producto_dto = ProductoDTO()
productos_dto = ProductoDTO(many=True)