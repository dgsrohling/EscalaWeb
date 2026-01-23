"""
Modelo de Servidor/Plantonista
"""

from datetime import datetime
from utils.database import db


class Servidor(db.Model):
    """
    Modelo de Servidor/Plantonista
    
    Attributes:
        id: ID único do servidor
        matricula: Matrícula do servidor (única)
        nome_completo: Nome completo do servidor
        tipo_grupo: Tipo de grupo (GERAL, SAUDE_17H, SAUDE_17H30)
        secretaria_id: ID da secretaria (apenas para tipo GERAL)
        telefone: Telefone de contato
        email: Email de contato
        ativo: Status do servidor (True/False)
        criado_em: Data e hora de criação
        atualizado_em: Data e hora da última atualização
    """
    
    __tablename__ = 'servidores'
    
    id = db.Column(db.Integer, primary_key=True)
    matricula = db.Column(db.String(20), unique=True, nullable=False, index=True)
    nome_completo = db.Column(db.String(200), nullable=False)
    tipo_grupo = db.Column(db.String(20), nullable=False, index=True)
    # tipo_grupo: 'GERAL', 'SAUDE_17H', 'SAUDE_17H30'
    
    # Relacionamento com secretaria (apenas para tipo GERAL)
    secretaria_id = db.Column(db.Integer, db.ForeignKey('secretarias.id'), nullable=True)
    
    # Contatos
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    
    # Status
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relacionamentos
    secretaria = db.relationship('Secretaria', back_populates='servidores')
    distribuicoes = db.relationship('EscalaDistribuicao', back_populates='servidor', lazy='dynamic')
    plantoes_realizados = db.relationship('PlantaoRealizado', back_populates='servidor', lazy='dynamic')
    
    def __repr__(self):
        return f'<Servidor {self.matricula} - {self.nome_completo}>'
    
    def to_dict(self):
        """
        Converte o servidor para dicionário
        
        Returns:
            dict: Dados do servidor
        """
        return {
            'id': self.id,
            'matricula': self.matricula,
            'nome_completo': self.nome_completo,
            'tipo_grupo': self.tipo_grupo,
            'tipo_grupo_display': self.get_tipo_grupo_display(),
            'secretaria_id': self.secretaria_id,
            'secretaria_nome': self.secretaria.nome if self.secretaria else None,
            'telefone': self.telefone,
            'email': self.email,
            'ativo': self.ativo,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
        }
    
    def get_tipo_grupo_display(self):
        """
        Retorna o nome amigável do tipo de grupo
        
        Returns:
            str: Nome amigável do tipo
        """
        tipos = {
            'GERAL': 'GERAL',
            'SAUDE_17H': 'SAÚDE 17h',
            'SAUDE_17H30': 'SAÚDE 17h30'
        }
        return tipos.get(self.tipo_grupo, self.tipo_grupo)
    
    def get_horario_sobreaviso(self):
        """
        Retorna o horário de sobreaviso do servidor
        
        Returns:
            dict: {'inicio': 'HH:MM', 'fim': 'HH:MM'}
        """
        horarios = {
            'GERAL': {'inicio': '17:00', 'fim': '08:00'},
            'SAUDE_17H': {'inicio': '17:00', 'fim': '08:00'},
            'SAUDE_17H30': {'inicio': '17:30', 'fim': '08:00'}
        }
        return horarios.get(self.tipo_grupo, {'inicio': '17:00', 'fim': '08:00'})
    
    @staticmethod
    def listar_ativos():
        """
        Lista apenas servidores ativos
        
        Returns:
            Query de servidores ativos
        """
        return Servidor.query.filter_by(ativo=True).order_by(Servidor.nome_completo)
    
    @staticmethod
    def listar_por_tipo_grupo(tipo_grupo, apenas_ativos=True):
        """
        Lista servidores de um tipo de grupo específico
        
        Args:
            tipo_grupo: Tipo de grupo (GERAL, SAUDE_17H, SAUDE_17H30)
            apenas_ativos: Se True, lista apenas ativos
            
        Returns:
            Query de servidores
        """
        query = Servidor.query.filter_by(tipo_grupo=tipo_grupo)
        if apenas_ativos:
            query = query.filter_by(ativo=True)
        return query.order_by(Servidor.nome_completo)
    
    @staticmethod
    def buscar_por_matricula(matricula):
        """
        Busca servidor por matrícula
        
        Args:
            matricula: Matrícula do servidor
            
        Returns:
            Servidor ou None
        """
        return Servidor.query.filter_by(matricula=matricula).first()
    
    def total_plantoes_mes(self, mes, ano):
        """
        Retorna o total de plantões realizados em um mês
        
        Args:
            mes: Mês (1-12)
            ano: Ano (YYYY)
            
        Returns:
            int: Quantidade de plantões
        """
        return self.plantoes_realizados.filter_by(
            competencia_mes=mes,
            competencia_ano=ano
        ).count()
    
    def total_horas_mes(self, mes, ano):
        """
        Retorna o total de horas trabalhadas em um mês
        
        Args:
            mes: Mês (1-12)
            ano: Ano (YYYY)
            
        Returns:
            float: Total de horas
        """
        plantoes = self.plantoes_realizados.filter_by(
            competencia_mes=mes,
            competencia_ano=ano
        ).all()
        
        total = sum(p.horas_trabalhadas or 0 for p in plantoes)
        return total