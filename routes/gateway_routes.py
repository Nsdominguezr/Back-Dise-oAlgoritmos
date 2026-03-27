from flask import Blueprint, request, jsonify, current_app, Response
import requests

# Creamos un Blueprint para mantener el orden
gateway_bp = Blueprint('gateway_bp', __name__)

# Atrapamos rutas con y sin sub-rutas adicionales
@gateway_bp.route('/api/<servicio>', defaults={'ruta': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@gateway_bp.route('/api/<servicio>/<path:ruta>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy(servicio, ruta):
    # 1. Verificar si el servicio solicitado existe en nuestra configuración
    microservicios = current_app.config['MICROSERVICIOS']
    if servicio not in microservicios:
        return jsonify({"error": f"El servicio '{servicio}' no está configurado en el Gateway"}), 404

    # 2. Construir la URL destino exacta
    base_url = microservicios[servicio]
    url_destino = f"{base_url}/{ruta}" if ruta else base_url

    # 3. Preparar los Headers (Excluimos 'Host' para no confundir al microservicio destino)
    headers_originales = {key: value for (key, value) in request.headers if key.lower() != 'host'}

    try:
        # 4. Reenviar la petición HTTP al microservicio correspondiente
        respuesta_ms = requests.request(
            method=request.method,
            url=url_destino,
            headers=headers_originales,
            data=request.get_data(), # Pasa el JSON (Body) intacto
            params=request.args,     # Pasa los Query Params (?id=1) intactos
            allow_redirects=False
        )
        
        # 5. Limpiar headers de respuesta que podrían causar conflictos
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers_respuesta = [
            (name, value) for (name, value) in respuesta_ms.raw.headers.items()
            if name.lower() not in excluded_headers
        ]
        
        # 6. Devolver la respuesta exacta de vuelta a Angular
        return Response(respuesta_ms.content, respuesta_ms.status_code, headers_respuesta)

    except requests.exceptions.ConnectionError:
        # Si el microservicio destino está apagado o fallando
        return jsonify({"error": f"El microservicio de '{servicio}' está caído o inaccesible."}), 503