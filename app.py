from flask import Flask
from flask_cors import CORS
from config import Config
from routes.gateway_routes import gateway_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Habilitar CORS globalmente para que Angular pueda hacer peticiones sin ser bloqueado
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Registrar el enrutador
    app.register_blueprint(gateway_bp)

    return app

app = create_app()

if __name__ == '__main__':
    print(f"🚀 API Gateway iniciando en el puerto {app.config['PORT']}...")
    print("Enrutando tráfico hacia:")
    for svc, url in app.config['MICROSERVICIOS'].items():
        print(f" - /api/{svc} -> {url}")
        
    app.run(host='0.0.0.0', port=app.config['PORT'], debug=True, ssl_context='adhoc')