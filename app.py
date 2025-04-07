# Remova as linhas de import eventlet e monkey_patch no início

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO, emit
from config import Config

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
# Altere para threading ou tente gevent (precisa instalar gevent primeiro)
socketio = SocketIO(async_mode='threading', cors_allowed_origins="*")

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions with app
    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app)
    
    # Import and register blueprints
    from routes.auth_routes import auth_bp
    from routes.fila_routes import fila_bp
    from routes.servico_routes import servico_bp
    from routes.agendamento_routes import agendamento_bp
    from services.fila_service import FilaService
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(fila_bp, url_prefix='/api/fila')
    app.register_blueprint(servico_bp, url_prefix='/api/servico')
    app.register_blueprint(agendamento_bp, url_prefix='/api/agendamento')
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
    # SocketIO events
    @socketio.on('connect_fila')
    def handle_connect(data):
        servico_id = data.get('servico_id')
        emit('fila_atualizada', FilaService.listar_fila(servico_id), broadcast=True)
        
    return app

# Application entry point
if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true',
        use_reloader=False
    )