from app import db
from datetime import datetime

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    tipo = db.Column(db.String(20), default="normal")  # normal, prioritario
    token_app = db.Column(db.String(255))
    senha = db.Column(db.String(120))

class LocalAtendimento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    endereco = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    servicos = db.relationship('Servico', backref='local', lazy=True)

class Servico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(255))
    duracao_media = db.Column(db.Integer, nullable=False)
    local_id = db.Column(db.Integer, db.ForeignKey('local_atendimento.id'), nullable=False)
    filas = db.relationship('Fila', backref='servico', lazy=True)
    slots = db.relationship('SlotAgendamento', backref='servico', lazy=True)

class Fila(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    id_servico = db.Column(db.Integer, db.ForeignKey('servico.id'), nullable=False)
    senha = db.Column(db.String(10), nullable=False)
    prioridade = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="aguardando")
    horario_entrada = db.Column(db.DateTime, default=datetime.utcnow)
    horario_estimado = db.Column(db.DateTime)
    posicao = db.Column(db.Integer, nullable=False)
    ultima_notificacao = db.Column(db.DateTime)

class SlotAgendamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_servico = db.Column(db.Integer, db.ForeignKey('servico.id'), nullable=False)
    data_horario = db.Column(db.DateTime, nullable=False)  # Data e hora do slot
    capacidade_maxima = db.Column(db.Integer, nullable=False)  # Nº de pacientes por slot
    capacidade_atual = db.Column(db.Integer, default=0)  # Nº atual de agendamentos
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))  # Quem agendou (null se slot aberto)
    status = db.Column(db.String(20), default="aberto")  # aberto, reservado, concluido

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    id_fila = db.Column(db.Integer, db.ForeignKey('fila.id'), nullable=True)
    id_slot = db.Column(db.Integer, db.ForeignKey('slot_agendamento.id'), nullable=True)
    nota = db.Column(db.Integer, nullable=False)
    comentario = db.Column(db.String(255))
    data = db.Column(db.DateTime, default=datetime.utcnow)