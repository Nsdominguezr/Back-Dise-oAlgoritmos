from flask_marshmallow import Marshmallow
from models.inventory_model import Inventario, MovimientoInventario

ma = Marshmallow()

class MovimientoDTO(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = MovimientoInventario
        fields = ("id", "tipo_movimiento", "cantidad", "fecha", "observacion", "usuario_id")

class InventarioDTO(ma.SQLAlchemyAutoSchema):
    # Anidamos los movimientos para poder ver el historial al consultar el stock
    movimientos = ma.Nested(MovimientoDTO, many=True)
    
    class Meta:
        model = Inventario
        fields = ("id", "sede_id", "producto_id", "cantidad", "movimientos")

inventario_dto = InventarioDTO()
inventarios_dto = InventarioDTO(many=True)