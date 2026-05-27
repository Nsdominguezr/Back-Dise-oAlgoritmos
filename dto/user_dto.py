"""Módulo de DTOs (Data Transfer Objects) de usuarios.

Contiene los esquemas de serialización para Usuario y Rol.
"""

from flask_marshmallow import Marshmallow
from models.user_model import Usuario, Rol

ma = Marshmallow()


class RolDTO(ma.SQLAlchemyAutoSchema):
    """Esquema de serialización para el modelo Rol."""

    class Meta:
        model = Rol
        fields = ("id", "nombre")


class UsuarioDTO(ma.SQLAlchemyAutoSchema):
    """Esquema de serialización para el modelo Usuario.

    Anida el DTO del rol y excluye el password_hash para seguridad.
    """
    rol = ma.Nested(RolDTO)

    class Meta:
        model = Usuario
        # Excluimos el password_hash para que nunca viaje en la respuesta JSON.
        exclude = ("password_hash",)


# Instancias para usar en los controladores.
usuario_dto = UsuarioDTO()
usuarios_dto = UsuarioDTO(many=True)