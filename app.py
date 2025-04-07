from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token
from flask_socketio import SocketIO, emit

# Crie a aplicação Flask
app = Flask(__name__)

# Configurações básicas
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'sua_chave_secreta'  # Altere para uma chave segura em produção

# Inicialize as extensões
db = SQLAlchemy(app)
jwt = JWTManager(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Modelo simples de Usuário
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(120), nullable=False)
    tipo = db.Column(db.String(50), default='normal')

    def __repr__(self):
        return f'<Usuario {self.email}>'

# Crie as tabelas no banco de dados
with app.app_context():
    db.create_all()

# Rota de login com JWT
@app.route('/api/auth/login', methods=['POST'])
def login():
    dados = request.get_json()
    email = dados.get('email')
    senha = dados.get('senha')

    if not email or not senha:
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400

    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario or usuario.senha != senha:
        return jsonify({"erro": "Credenciais inválidas"}), 401

    token = create_access_token(identity={'id': usuario.id, 'tipo': usuario.tipo})
    return jsonify({
        "access_token": token,
        "id": usuario.id,
        "tipo": usuario.tipo
    }), 200

# Evento básico do SocketIO para teste
@socketio.on('connect_fila')
def handle_connect(data):
    print("Cliente conectado ao SocketIO:", data)
    emit('fila_atualizada', {"mensagem": "Conexão estabelecida"}, broadcast=True)

# Função para adicionar um usuário de teste
def adicionar_usuario_teste():
    with app.app_context():
        usuario = Usuario.query.filter_by(email='edmannews5@gmail.com').first()
        if not usuario:
            usuario = Usuario(email='edmannews5@gmail.com', senha='123456', tipo='normal')
            db.session.add(usuario)
            db.session.commit()
            print("Usuário de teste criado com ID:", usuario.id)
        else:
            print("Usuário já existe com ID:", usuario.id)

if __name__ == '__main__':
    adicionar_usuario_teste()  # Adiciona o usuário ao iniciar
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)  # Use socketio.run para suportar WebSocket