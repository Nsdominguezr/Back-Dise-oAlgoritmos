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
        
        # Sprint 4 5003
        "inventario": os.getenv("INVENTORY_SERVICE_URL", "http://127.0.0.1:5003/api/inventario"),
        
        # Sprint 5 y 6 5004
        "pedidos": os.getenv("ORDERS_SERVICE_URL", "http://127.0.0.1:5004/api/pedidos")
    }