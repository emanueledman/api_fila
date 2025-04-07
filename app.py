from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO, emit
from config import Config

db = SQLAlchemy()
jwt = JWTManager()
socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    # Importações movidas para dentro da função para evitar circular import
    from routes.auth_routes import auth_bp
    from routes.fila_routes import fila_bp
    from routes.servico_routes import servico_bp
    from routes.agendamento_routes import agendamento_bp
    from services.fila_service import FilaService  # Importado aqui

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(fila_bp, url_prefix='/api/fila')
    app.register_blueprint(servico_bp, url_prefix='/api/servico')
    app.register_blueprint(agendamento_bp, url_prefix='/api/agendamento')

    with app.app_context():
        db.create_all()

    @socketio.on('connect_fila')
    def handle_connect(data):
        servico_id = data.get('servico_id')
        emit('fila_atualizada', FilaService.listar_fila(servico_id), broadcast=True)

    return app

if __name__ == '__main__':
    app = create_app()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)