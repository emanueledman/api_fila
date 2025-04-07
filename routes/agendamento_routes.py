from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models.fila_models import SlotAgendamento, Feedback
from services.agendamento_service import AgendamentoService
from services.troca_service import TrocaService  # Novo
from datetime import datetime

agendamento_bp = Blueprint('agendamento', __name__)

@agendamento_bp.route('/servico/<int:servico_id>/slot', methods=['POST'])
@jwt_required()
def criar_slot(servico_id):
    identity = get_jwt_identity()
    if identity['tipo'] != 'admin':
        return jsonify({"erro": "Apenas admin pode criar slots"}), 403
    
    dados = request.get_json()
    data_horario = datetime.fromisoformat(dados.get('data_horario'))
    capacidade_maxima = dados.get('capacidade_maxima')
    if not all([data_horario, capacidade_maxima]):
        return jsonify({"erro": "Data/horário e capacidade são obrigatórios"}), 400
    
    slot = AgendamentoService.criar_slot(servico_id, data_horario, capacidade_maxima)
    return jsonify({"mensagem": "Slot criado", "id": slot.id}), 201

@agendamento_bp.route('/servico/<int:servico_id>/slots', methods=['GET'])
def listar_slots(servico_id):
    slots = AgendamentoService.listar_slots_disponiveis(servico_id)
    return jsonify([{"id": s.id, "data_horario": s.data_horario.isoformat(), "capacidade_maxima": s.capacidade_maxima, "capacidade_atual": s.capacidade_atual} for s in slots])

@agendamento_bp.route('/slot/<int:slot_id>/reservar', methods=['POST'])
@jwt_required()
def reservar_slot(slot_id):
    identity = get_jwt_identity()
    try:
        slot = AgendamentoService.reservar_slot(slot_id, identity['id'])
        return jsonify({"mensagem": "Slot reservado", "data_horario": slot.data_horario.isoformat()}), 201
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400

@agendamento_bp.route('/slot/<int:slot_id>/cancelar', methods=['DELETE'])
@jwt_required()
def cancelar_slot(slot_id):
    identity = get_jwt_identity()
    try:
        AgendamentoService.cancelar_slot(slot_id, identity['id'])
        return jsonify({"mensagem": "Slot cancelado"})
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400

@agendamento_bp.route('/slot/<int:slot_id>/feedback', methods=['POST'])
@jwt_required()
def dar_feedback_slot(slot_id):
    identity = get_jwt_identity()
    slot = SlotAgendamento.query.get_or_404(slot_id)
    if slot.usuario_id != identity['id']:
        return jsonify({"erro": "Acesso negado"}), 403
    
    dados = request.get_json()
    nota, comentario = dados.get('nota'), dados.get('comentario')
    if not nota or nota not in range(0, 6):
        return jsonify({"erro": "Nota deve ser entre 0 e 5"}), 400
    
    feedback = Feedback(id_usuario=identity['id'], id_slot=slot_id, nota=nota, comentario=comentario)
    db.session.add(feedback)
    db.session.commit()
    return jsonify({"mensagem": "Feedback registrado"}), 201

# Novas rotas para troca
@agendamento_bp.route('/slot/<int:slot_id>/oferecer-troca', methods=['POST'])
@jwt_required()
def oferecer_troca_slot(slot_id):
    identity = get_jwt_identity()
    try:
        slot = TrocaService.oferecer_troca_slot(slot_id, identity['id'])
        return jsonify({"mensagem": f"Slot {slot.data_horario} oferecido para troca"}), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400

@agendamento_bp.route('/servico/<int:servico_id>/trocas-disponiveis', methods=['GET'])
@jwt_required()
def listar_trocas_disponiveis_slots(servico_id):
    trocas = TrocaService.listar_trocas_disponiveis_slots(servico_id)
    return jsonify([{"id": t.id, "data_horario": t.data_horario.isoformat()} for t in trocas])

@agendamento_bp.route('/slot/<int:slot_origem_id>/trocar/<int:slot_destino_id>', methods=['POST'])
@jwt_required()
def trocar_slot(slot_origem_id, slot_destino_id):
    identity = get_jwt_identity()
    try:
        resultado = TrocaService.trocar_slot(slot_origem_id, slot_destino_id, identity['id'])
        return jsonify({"mensagem": "Troca realizada com sucesso", "detalhes": {
            "slot_origem": {"data_horario": resultado["slot_origem"].data_horario.isoformat()},
            "slot_destino": {"data_horario": resultado["slot_destino"].data_horario.isoformat()}
        }}), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400