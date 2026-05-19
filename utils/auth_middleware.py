from flask import request, jsonify, current_app
import jwt
from functools import wraps

def admin_global_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({'mensaje': 'Token faltante.'}), 401

        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            if data.get('rol') != 'Admin Global':
                return jsonify({'mensaje': 'Requiere privilegios de Admin Global.'}), 403
        except Exception as e:
            return jsonify({'mensaje': 'Token inválido o expirado.'}), 401

        return f(*args, **kwargs)
    return decorated