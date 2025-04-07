from extensions import db
from models.fila_models import SlotAgendamento, Servico, Usuario
from datetime import datetime
import requests

class AgendamentoService:
    SMS_API_URL = "https://api.sms.com/send"
    SMS_API_KEY = "sua_chave"
    EMAIL_API_URL = "https://api.email.com/send"
    EMAIL_API_KEY = "sua_chave"

    @staticmethod
    def enviar_notificacao(usuario, mensagem):
        if usuario.telefone:
            requests.post(AgendamentoService.SMS_API_URL, json={
                "to": usuario.telefone,
                "message": mensagem,
                "api_key": AgendamentoService.SMS_API_KEY
            })
        if usuario.email:
            requests.post(AgendamentoService.EMAIL_API_URL, json={
                "to": usuario.email,
                "subject": "Atualização de Agendamento",
                "body": mensagem,
                "api_key": AgendamentoService.EMAIL_API_KEY
            })
        if usuario.token_app:
            requests.post("https://fcm.googleapis.com/fcm/send", json={
                "to": usuario.token_app,
                "notification": {"title": "Agendamento", "body": mensagem}
            }, headers={"Authorization": "key=sua_chave_fcm"})

    @staticmethod
    def criar_slot(servico_id, data_horario, capacidade_maxima):
        slot = SlotAgendamento(
            id_servico=servico_id,
            data_horario=data_horario,
            capacidade_maxima=capacidade_maxima
        )
        db.session.add(slot)
        db.session.commit()
        return slot

    @staticmethod
    def reservar_slot(slot_id, usuario_id):
        slot = SlotAgendamento.query.get_or_404(slot_id)
        if slot.status != "aberto" or slot.capacidade_atual >= slot.capacidade_maxima:
            raise ValueError("Slot indisponível ou lotado")
        
        slot.usuario_id = usuario_id
        slot.capacidade_atual += 1
        slot.status = "reservado" if slot.capacidade_atual < slot.capacidade_maxima else "concluido"
        db.session.commit()
        
        usuario = Usuario.query.get(usuario_id)
        AgendamentoService.enviar_notificacao(usuario, f"Agendamento confirmado para {slot.data_horario}")
        return slot

    @staticmethod
    def listar_slots_disponiveis(servico_id):
        return SlotAgendamento.query.filter_by(id_servico=servico_id, status="aberto").all()

    @staticmethod
    def cancelar_slot(slot_id, usuario_id):
        slot = SlotAgendamento.query.get_or_404(slot_id)
        if slot.usuario_id != usuario_id and slot.status != "reservado":
            raise ValueError("Slot não pode ser cancelado")
        
        slot.usuario_id = None
        slot.capacidade_atual -= 1
        slot.status = "aberto"
        db.session.commit()
        
        usuario = Usuario.query.get(usuario_id)
        AgendamentoService.enviar_notificacao(usuario, f"Agendamento cancelado para {slot.data_horario}")