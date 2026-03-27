from flask_marshmallow import Marshmallow
from models.user_model import Usuario, Rol

ma = Marshmallow()

class RolDTO(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Rol
        fields = ("id", "nombre")

class UsuarioDTO(ma.SQLAlchemyAutoSchema):
    rol = ma.Nested(RolDTO) # Anidamos el DTO del rol

    class Meta:
        model = Usuario
        # Excluimos el password_hash para que nunca viaje en la respuesta JSON
        exclude = ("password_hash",)

# Instancias para usar en los controladores
usuario_dto = UsuarioDTO()
usuarios_dto = UsuarioDTO(many=True)