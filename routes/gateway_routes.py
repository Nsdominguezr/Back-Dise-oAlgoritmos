"""Módulo de rutas del API Gateway.

Gestiona el enrutamiento de peticiones hacia los microservicios correspondientes.
"""

from flask import Blueprint, request, jsonify, current_app, Response
import requests

gateway_bp = Blueprint('gateway_bp', __name__)


@gateway_bp.route(
    '/api/<servicio>',
    defaults={'ruta': ''},
    methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
)
@gateway_bp.route('/api/<servicio>/<path:ruta>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy(servicio, ruta):
    """Redirige las peticiones al microservicio correspondiente.

    Args:
        servicio: Nombre del microservicio a invocar.
        ruta: Ruta específica dentro del microservicio (opcional).

    Returns:
        Respuesta del microservicio o mensaje de error.
    """
    microservicios = current_app.config['MICROSERVICIOS']
    if servicio not in microservicios:
        return jsonify(
            {"error": f"El servicio '{servicio}' no está configurado en el Gateway"}
        ), 404

    base_url = microservicios[servicio]
    url_destino = f"{base_url}/{ruta}" if ruta else base_url

    headers_originales = {
        key: value for (key, value) in request.headers if key.lower() != 'host'
    }

    try:
        respuesta_ms = requests.request(
            method=request.method,
            url=url_destino,
            headers=headers_originales,
            data=request.get_data(),
            params=request.args,
            allow_redirects=False,
            stream=True  # Para archivos grandes o respuestas binarias.
        )

        excluded_headers = [
            'content-encoding',
            'content-length',
            'transfer-encoding',
            'connection'
        ]
        headers_respuesta = [
            (name, value) for (name, value) in respuesta_ms.raw.headers.items()
            if name.lower() not in excluded_headers
        ]

        return Response(
            respuesta_ms.content,
            respuesta_ms.status_code,
            headers_respuesta
        )

    except requests.exceptions.ConnectionError:
        return jsonify(
            {"error": f"El microservicio de '{servicio}' está caído o inaccesible."}
        ), 503