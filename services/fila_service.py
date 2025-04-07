# services/fila_service.py
from extensions import db
# resto do código
from models.fila_models import Fila, Servico, Usuario
from datetime import datetime, timedelta
import requests

class FilaService:
    SMS_API_URL = "https://api.sms.com/send"
    SMS_API_KEY = "sua_chave"
    EMAIL_API_URL = "https://api.email.com/send"
    EMAIL_API_KEY = "sua_chave"

    @staticmethod
    def gerar_senha(servico_id):
        ultimo = Fila.query.filter_by(id_servico=servico_id).order_by(Fila.id.desc()).first()
        numero = int(ultimo.senha[1:]) + 1 if ultimo else 1
        return f"A{numero:03d}"

    @staticmethod
    def calcular_horario_estimado(servico_id, posicao):
        servico = Servico.query.get_or_404(servico_id)
        pessoas_aguardando = Fila.query.filter_by(id_servico=servico_id, status="aguardando")\
            .order_by(Fila.prioridade.desc(), Fila.posicao).all()
        minutos_totais = sum(servico.duracao_media for _ in pessoas_aguardando[:posicao-1])
        return datetime.utcnow() + timedelta(minutes=minutos_totais)

    @staticmethod
    def enviar_notificacao(usuario, mensagem):
        if usuario.telefone:
            requests.post(FilaService.SMS_API_URL, json={
                "to": usuario.telefone,
                "message": mensagem,
                "api_key": FilaService.SMS_API_KEY
            })
        if usuario.email:
            requests.post(FilaService.EMAIL_API_URL, json={
                "to": usuario.email,
                "subject": "Atualização da Fila",
                "body": mensagem,
                "api_key": FilaService.EMAIL_API_KEY
            })
        if usuario.token_app:
            requests.post("https://fcm.googleapis.com/fcm/send", json={
                "to": usuario.token_app,
                "notification": {"title": "Fila Virtual", "body": mensagem}
            }, headers={"Authorization": "key=sua_chave_fcm"})

    @staticmethod
    def adicionar_pessoa(servico_id, usuario_id):
        usuario = Usuario.query.get_or_404(usuario_id)
        servico = Servico.query.get_or_404(servico_id)
        
        if Fila.query.filter_by(id_usuario=usuario_id, id_servico=servico_id, status="aguardando").first():
            raise ValueError("Usuário já está nesta fila")
        
        prioridade = 1 if usuario.tipo == "prioritario" else 0
        ultima_posicao = db.session.query(db.func.max(Fila.posicao)).filter_by(id_servico=servico_id, status="aguardando").scalar() or 0
        senha = FilaService.gerar_senha(servico_id)
        horario_estimado = FilaService.calcular_horario_estimado(servico_id, ultima_posicao + 1)
        
        nova_fila = Fila(
            id_usuario=usuario_id,
            id_servico=servico_id,
            senha=senha,
            prioridade=prioridade,
            posicao=ultima_posicao + 1,
            horario_estimado=horario_estimado
        )
        db.session.add(nova_fila)
        db.session.commit()
        
        FilaService.atualizar_posicoes(servico_id)
        FilaService.enviar_notificacao(usuario, f"Você entrou na fila. Senha: {senha}. Horário estimado: {horario_estimado}")
        return nova_fila

    @staticmethod
    def chamar_proximo(servico_id):
        pessoa = Fila.query.filter_by(id_servico=servico_id, status="aguardando")\
            .order_by(Fila.prioridade.desc(), Fila.posicao).first()
        if not pessoa:
            raise ValueError("Fila vazia")
        
        pessoa.status = "chamado"
        usuario = Usuario.query.get(pessoa.id_usuario)
        db.session.commit()
        
        FilaService.atualizar_posicoes(servico_id)
        FilaService.enviar_notificacao(usuario, f"Você foi chamado! Senha: {pessoa.senha}")
        return pessoa

    @staticmethod
    def atualizar_posicoes(servico_id):
        pessoas = Fila.query.filter_by(id_servico=servico_id, status="aguardando")\
            .order_by(Fila.prioridade.desc(), Fila.posicao).all()
        for i, pessoa in enumerate(pessoas, 1):
            old_posicao = pessoa.posicao
            pessoa.posicao = i
            pessoa.horario_estimado = FilaService.calcular_horario_estimado(servico_id, i)
            if old_posicao != i and (datetime.utcnow() - (pessoa.ultima_notificacao or datetime.min)).total_seconds() > 300:
                usuario = Usuario.query.get(pessoa.id_usuario)
                FilaService.enviar_notificacao(usuario, f"Sua posição mudou para {i}. Horário estimado: {pessoa.horario_estimado}")
                pessoa.ultima_notificacao = datetime.utcnow()
        db.session.commit()

    @staticmethod
    def listar_fila(servico_id):
        return Fila.query.filter_by(id_servico=servico_id, status="aguardando")\
            .order_by(Fila.prioridade.desc(), Fila.posicao).all()

    @staticmethod
    def gerar_relatorio(servico_id):
        filas = Fila.query.filter_by(id_servico=servico_id).all()
        feedbacks = db.session.query(Feedback).join(Fila).filter(Fila.id_servico == servico_id).all()
        
        tempo_medio_espera = sum((f.horario_estimado - f.horario_entrada).total_seconds() / 60 for f in filas if f.horario_estimado) / len(filas) if filas else 0
        total_atendimentos = len([f for f in filas if f.status == "atendido"])
        nota_media = sum(f.nota for f in feedbacks) / len(feedbacks) if feedbacks else 0
        
        return {
            "tempo_medio_espera_min": tempo_medio_espera,
            "total_atendimentos": total_atendimentos,
            "nota_media": nota_media,
            "feedbacks": [{"nota": f.nota, "comentario": f.comentario} for f in feedbacks]
        }