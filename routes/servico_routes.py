from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models.fila_models import LocalAtendimento, Servico

servico_bp = Blueprint('servico', __name__)

@servico_bp.route('/local', methods=['POST'])
@jwt_required()
def criar_local():
    identity = get_jwt_identity()
    if identity['tipo'] != 'admin':
        return jsonify({"erro": "Apenas admin pode criar locais"}), 403
    
    dados = request.get_json()
    nome, endereco, tipo = dados.get('nome'), dados.get('endereco'), dados.get('tipo')
    if not all([nome, endereco, tipo]):
        return jsonify({"erro": "Todos os campos são obrigatórios"}), 400
    
    local = LocalAtendimento(nome=nome, endereco=endereco, tipo=tipo)
    db.session.add(local)
    db.session.commit()
    return jsonify({"mensagem": "Local criado", "id": local.id}), 201

@servico_bp.route('/local/<int:local_id>/servico', methods=['POST'])
@jwt_required()
def criar_servico(local_id):
    identity = get_jwt_identity()
    if identity['tipo'] != 'admin':
        return jsonify({"erro": "Apenas admin pode criar serviços"}), 403
    
    dados = request.get_json()
    nome, descricao, duracao_media = dados.get('nome'), dados.get('descricao'), dados.get('duracao_media')
    if not all([nome, duracao_media]):
        return jsonify({"erro": "Nome e duração média são obrigatórios"}), 400
    
    servico = Servico(nome=nome, descricao=descricao, duracao_media=duracao_media, local_id=local_id)
    db.session.add(servico)
    db.session.commit()
    return jsonify({"mensagem": "Serviço criado", "id": servico.id}), 201

@servico_bp.route('/locais', methods=['GET'])
def listar_locais():
    locais = LocalAtendimento.query.all()
    return jsonify([{"id": l.id, "nome": l.nome, "endereco": l.endereco, "tipo": l.tipo} for l in locais])

@servico_bp.route('/local/<int:local_id>/servicos', methods=['GET'])
def listar_servicos(local_id):
    servicos = Servico.query.filter_by(local_id=local_id).all()
    return jsonify([{"id": s.id, "nome": s.nome, "descricao": s.descricao, "duracao_media": s.duracao_media} for s in servicos])