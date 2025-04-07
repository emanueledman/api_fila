from app import db
from models.fila_models import Fila, SlotAgendamento, Usuario
from services.fila_service import FilaService
from services.agendamento_service import AgendamentoService
from datetime import datetime

class TrocaService:
    @staticmethod
    def oferecer_troca_fila(fila_id, usuario_id):
        fila = Fila.query.get_or_404(fila_id)
        if fila.id_usuario != usuario_id or fila.status != "aguardando":
            raise ValueError("Você não pode oferecer esta vaga para troca")
        
        fila.troca_disponivel = True
        db.session.commit()
        usuario = Usuario.query.get(usuario_id)
        FilaService.enviar_notificacao(usuario, f"Sua vaga (Senha: {fila.senha}) está disponível para troca.")
        return fila

    @staticmethod
    def oferecer_troca_slot(slot_id, usuario_id):
        slot = SlotAgendamento.query.get_or_404(slot_id)
        if slot.usuario_id != usuario_id or slot.status != "reservado":
            raise ValueError("Você não pode oferecer este slot para troca")
        
        slot.troca_disponivel = True
        db.session.commit()
        usuario = Usuario.query.get(usuario_id)
        AgendamentoService.enviar_notificacao(usuario, f"Seu agendamento ({slot.data_horario}) está disponível para troca.")
        return slot

    @staticmethod
    def trocar_posicao_fila(fila_origem_id, fila_destino_id, usuario_origem_id):
        fila_origem = Fila.query.get_or_404(fila_origem_id)
        fila_destino = Fila.query.get_or_404(fila_destino_id)
        
        # Validações
        if fila_origem.id_usuario != usuario_origem_id:
            raise ValueError("Você só pode trocar sua própria vaga")
        if not fila_destino.troca_disponivel:
            raise ValueError("A vaga destino não está disponível para troca")
        if fila_origem.id_servico != fila_destino.id_servico or fila_origem.status != "aguardando" or fila_destino.status != "aguardando":
            raise ValueError("Troca inválida: serviços ou status incompatíveis")
        
        # Troca de usuários e posições
        usuario_origem = fila_origem.id_usuario
        usuario_destino = fila_destino.id_usuario
        posicao_origem = fila_origem.posicao
        posicao_destino = fila_destino.posicao
        
        fila_origem.id_usuario = usuario_destino
        fila_origem.posicao = posicao_destino
        fila_origem.troca_disponivel = False
        
        fila_destino.id_usuario = usuario_origem
        fila_destino.posicao = posicao_origem
        fila_destino.troca_disponivel = False
        
        db.session.commit()
        
        # Atualiza a fila e notifica
        FilaService.atualizar_posicoes(fila_origem.id_servico)
        usuario_o = Usuario.query.get(usuario_origem)
        usuario_d = Usuario.query.get(usuario_destino)
        FilaService.enviar_notificacao(usuario_o, f"Troca realizada! Sua nova senha é {fila_destino.senha}, posição {fila_destino.posicao}.")
        FilaService.enviar_notificacao(usuario_d, f"Troca realizada! Sua nova senha é {fila_origem.senha}, posição {fila_origem.posicao}.")
        
        return {"fila_origem": fila_origem, "fila_destino": fila_destino}

    @staticmethod
    def trocar_slot(slot_origem_id, slot_destino_id, usuario_origem_id):
        slot_origem = SlotAgendamento.query.get_or_404(slot_origem_id)
        slot_destino = SlotAgendamento.query.get_or_404(slot_destino_id)
        
        # Validações
        if slot_origem.usuario_id != usuario_origem_id:
            raise ValueError("Você só pode trocar seu próprio slot")
        if not slot_destino.troca_disponivel:
            raise ValueError("O slot destino não está disponível para troca")
        if slot_origem.id_servico != slot_destino.id_servico or slot_origem.status != "reservado" or slot_destino.status != "reservado":
            raise ValueError("Troca inválida: serviços ou status incompatíveis")
        
        # Troca de usuários
        usuario_origem = slot_origem.usuario_id
        usuario_destino = slot_destino.usuario_id
        
        slot_origem.usuario_id = usuario_destino
        slot_origem.troca_disponivel = False
        slot_destino.usuario_id = usuario_origem
        slot_destino.troca_disponivel = False
        
        db.session.commit()
        
        # Notifica
        usuario_o = Usuario.query.get(usuario_origem)
        usuario_d = Usuario.query.get(usuario_destino)
        AgendamentoService.enviar_notificacao(usuario_o, f"Troca realizada! Novo agendamento: {slot_destino.data_horario}.")
        AgendamentoService.enviar_notificacao(usuario_d, f"Troca realizada! Novo agendamento: {slot_origem.data_horario}.")
        
        return {"slot_origem": slot_origem, "slot_destino": slot_destino}

    @staticmethod
    def listar_trocas_disponiveis_fila(servico_id):
        return Fila.query.filter_by(id_servico=servico_id, status="aguardando", troca_disponivel=True).all()

    @staticmethod
    def listar_trocas_disponiveis_slots(servico_id):
        return SlotAgendamento.query.filter_by(id_servico=servico_id, status="reservado", troca_disponivel=True).all()