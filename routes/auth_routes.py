from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.fila_models import Usuario
from extensions import db, jwt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    dados = request.get_json()
    nome, telefone, email, senha = dados.get('nome'), dados.get('telefone'), dados.get('email'), dados.get('senha')
    tipo = dados.get('tipo', 'normal')
    
    if not all([nome, telefone, email, senha]):
        return jsonify({"erro": "Todos os campos são obrigatórios"}), 400
        
    if Usuario.query.filter_by(email=email).first():
        return jsonify({"erro": "Email já registrado"}), 409
        
    usuario = Usuario(nome=nome, telefone=telefone, email=email, senha=senha, tipo=tipo)  # Hash senha em produção
    db.session.add(usuario)
    db.session.commit()
    
    token = create_access_token(identity={"id": usuario.id, "tipo": usuario.tipo})
    return jsonify({"mensagem": "Usuário registrado", "token": token}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    dados = request.get_json()
    email, senha = dados.get('email'), dados.get('senha')
    
    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario or usuario.senha != senha:  # Compare hash em produção
        return jsonify({"erro": "Credenciais inválidas"}), 401
        
    token = create_access_token(identity={"id": usuario.id, "tipo": usuario.tipo})
    return jsonify({"token": token})