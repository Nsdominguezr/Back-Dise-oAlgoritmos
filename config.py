import os

class Config:
    # Puerto donde correrá el Gateway
    PORT = 8000
    
    # Diccionario de Enrutamiento: Mapea la ruta hacia el microservicio real
    MICROSERVICIOS = {
        # Todo lo que llegue a /api/auth se va al puerto 5001
        "auth": os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:5001/api/auth"),
        
        # Todo lo que llegue a /api/sedes o /api/productos se va al puerto 5002
        "sedes": os.getenv("CATALOG_SERVICE_URL", "http://127.0.0.1:5002/api/sedes"),
        "productos": os.getenv("CATALOG_SERVICE_URL", "http://127.0.0.1:5002/api/productos"),
        
        # Futuros microservicios (Sprints 4 y 5):
        # "inventario": "http://127.0.0.1:5003/api/inventario",
        # "pedidos": "http://127.0.0.1:5004/api/pedidos"
    }