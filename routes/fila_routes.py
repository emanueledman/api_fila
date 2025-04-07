from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models.fila_models import Fila, Feedback
from services.fila_service import FilaService

fila_bp = Blueprint('fila', __name__)

@fila_bp.route('/servico/<int:servico_id>/entrar', methods=['POST'])
@jwt_required()
def entrar_fila(servico_id):
    identity = get_jwt_identity()
    try:
        fila = FilaService.adicionar_pessoa(servico_id, identity['id'])
        return jsonify({
            "mensagem": "Entrou na fila",
            "fila": {"id": fila.id, "senha": fila.senha, "posicao": fila.posicao, "horario_estimado": fila.horario_estimado.isoformat()}
        }), 201
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400

@fila_bp.route('/servico/<int:servico_id>', methods=['GET'])
def listar_fila(servico_id):
    pessoas = FilaService.listar_fila(servico_id)
    return jsonify([{"id": p.id, "senha": p.senha, "posicao": p.posicao, "prioridade": p.prioridade} for p in pessoas])

@fila_bp.route('/servico/<int:servico_id>/monitor', methods=['GET'])
def monitor_fila(servico_id):
    atual = Fila.query.filter_by(id_servico=servico_id, status="chamado").order_by(Fila.horario_entrada.desc()).first()
    proximos = FilaService.listar_fila(servico_id)[:5]  # Próximos 5
    return jsonify({
        "atual": {"senha": atual.senha} if atual else None,
        "proximos": [{"senha": p.senha, "posicao": p.posicao} for p in proximos]
    })

@fila_bp.route('/servico/<int:servico_id>/proximo', methods=['GET'])
@jwt_required()
def chamar_proximo(servico_id):
    identity = get_jwt_identity()
    if identity['tipo'] != 'admin':
        return jsonify({" erro": "Apenas admin pode chamar o próximo"}), 403
    
    try:
        pessoa = FilaService.chamar_proximo(servico_id)
        return jsonify({"mensagem": f"Chamado: {pessoa.senha}", "senha": pessoa.senha})
    except ValueError as e:
        return jsonify({"erro": str(e)}), 404

@fila_bp.route('/fila/<int:fila_id>/cancelar', methods=['DELETE'])
@jwt_required()
def cancelar_fila(fila_id):
    identity = get_jwt_identity()
    fila = Fila.query.get_or_404(fila_id)
    if fila.id_usuario != identity['id'] and identity['tipo'] != 'admin':
        return jsonify({"erro": "Acesso negado"}), 403
    
    fila.status = "cancelado"
    db.session.commit()
    FilaService.atualizar_posicoes(fila.id_servico)
    return jsonify({"mensagem": "Fila cancelada"})

@fila_bp.route('/fila/<int:fila_id>/feedback', methods=['POST'])
@jwt_required()
def dar_feedback(fila_id):
    identity = get_jwt_identity()
    fila = Fila.query.get_or_404(fila_id)
    if fila.id_usuario != identity['id']:
        return jsonify({"erro": "Acesso negado"}), 403
    
    dados = request.get_json()
    nota, comentario = dados.get('nota'), dados.get('comentario')
    if not nota or nota not in range(0, 6):
        return jsonify({"erro": "Nota deve ser entre 0 e 5"}), 400
    
    feedback = Feedback(id_usuario=identity['id'], id_fila=fila_id, nota=nota, comentario=comentario)
    db.session.add(feedback)
    db.session.commit()
    return jsonify({"mensagem": "Feedback registrado"}), 201

@fila_bp.route('/servico/<int:servico_id>/relatorio', methods=['GET'])
@jwt_required()
def relatorio_fila(servico_id):
    identity = get_jwt_identity()
    if identity['tipo'] != 'admin':
        return jsonify({"erro": "Apenas admin pode ver relatórios"}), 403
    
    relatorio = FilaService.gerar_relatorio(servico_id)
    return jsonify(relatorio)