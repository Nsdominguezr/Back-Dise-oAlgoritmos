"""Aplicación Flask del servicio de pedidos.

Punto de entrada para el microservicio de gestión de pedidos, mesas y pagos.
"""

from flask import Flask
from config import Config
from models.orders_model import db, Pedido, Mesa
from controllers.orders_controller import orders_bp
from datetime import datetime, timedelta

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
app.register_blueprint(orders_bp)


def liberar_mesas_abandonadas():
    """Job que libera mesas con pedidos ABIERTOS sin actividad reciente."""
    with app.app_context():
        limite = datetime.utcnow() - timedelta(minutes=5)
        pedidos_abandonados = Pedido.query.filter(
            Pedido.estado == 'ABIERTO',
            Pedido.ultima_actividad < limite
        ).all()

        for pedido in pedidos_abandonados:
            mesa = Mesa.query.get(pedido.mesa_id)
            if mesa and mesa.estado == 'OCUPADA':
                mesa.estado = 'LIBRE'
            pedido.estado = 'CANCELADO'
            db.session.commit()


if __name__ == '__main__':
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=liberar_mesas_abandonadas, trigger='interval', minutes=5)
    scheduler.start()
    # Microservicio corre en el puerto 5004.
    app.run(host='0.0.0.0', port=5004, debug=True)