from flask import Flask, jsonify
from flask_socketio import emit
from extensions import db, jwt, socketio
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializa as extensões
    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Importa blueprints dentro da função para evitar importações circulares
    from routes.auth_routes import auth_bp
    from routes.fila_routes import fila_bp
    from routes.servico_routes import servico_bp
    from routes.agendamento_routes import agendamento_bp
    
    # Registra blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(fila_bp, url_prefix='/api/fila')
    app.register_blueprint(servico_bp, url_prefix='/api/servico')
    app.register_blueprint(agendamento_bp, url_prefix='/api/agendamento')
    
    @app.route('/')
    def index():
        return jsonify({'message': 'API funcionando. Use /api/auth, /api/fila, etc.'})
    
    # Cria as tabelas do banco de dados
    with app.app_context():
        db.create_all()
    
    return app

# Socket.IO event handlers - definido fora da função create_app para evitar problemas de escopo
@socketio.on('connect_fila')
def handle_connect(data):
    from services.fila_service import FilaService
    servico_id = data.get('servico_id')
    emit('fila_atualizada', FilaService.listar_fila(servico_id), broadcast=True)

# Cria a instância da aplicação
app = create_app()

# Ponto de entrada para execução local 
if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)