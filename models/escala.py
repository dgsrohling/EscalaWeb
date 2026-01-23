"""
Modelo de Escala
"""

from datetime import datetime
import calendar
from utils.database import db


class Escala(db.Model):
    """
    Modelo de Escala de Sobreaviso (Competência)
    
    Attributes:
        id: ID único da escala
        competencia_mes: Mês da escala (1-12)
        competencia_ano: Ano da escala (YYYY)
        tipo_escala: Tipo de escala (GERAL ou SAUDE)
        status: Status da escala (RASCUNHO, PUBLICADA, FINALIZADA, CANCELADA)
        criado_por_id: ID do usuário que criou
        observacao: Observações sobre a escala
        criada_em: Data e hora de criação
        atualizada_em: Data e hora da última atualização
        publicada_em: Data e hora de publicação
        finalizada_em: Data e hora de finalização
    """
    
    __tablename__ = 'escalas'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Competência
    competencia_mes = db.Column(db.Integer, nullable=False)  # 1-12
    competencia_ano = db.Column(db.Integer, nullable=False)  # YYYY
    
    # Tipo de escala
    tipo_escala = db.Column(db.String(20), nullable=False)
    # tipo_escala: 'GERAL' ou 'SAUDE'
    
    # Status
    status = db.Column(db.String(20), default='RASCUNHO', nullable=False)
    # status: 'RASCUNHO', 'PUBLICADA', 'FINALIZADA', 'CANCELADA'
    
    # Relacionamento com usuário
    criado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # Observações
    observacao = db.Column(db.Text)
    
    # Timestamps
    criada_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    atualizada_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    publicada_em = db.Column(db.DateTime)
    finalizada_em = db.Column(db.DateTime)
    
    # Relacionamentos
    criado_por = db.relationship('Usuario', back_populates='escalas_criadas')
    distribuicoes = db.relationship('EscalaDistribuicao', back_populates='escala', lazy='dynamic', cascade='all, delete-orphan')
    
    # Índice composto para busca rápida por competência
    __table_args__ = (
        db.Index('idx_competencia', 'competencia_mes', 'competencia_ano'),
    )
    
    def __repr__(self):
        return f'<Escala {self.competencia_mes}/{self.competencia_ano} - {self.tipo_escala}>'
    
    def to_dict(self):
        """
        Converte a escala para dicionário
        
        Returns:
            dict: Dados da escala
        """
        return {
            'id': self.id,
            'competencia_mes': self.competencia_mes,
            'competencia_ano': self.competencia_ano,
            'competencia_display': self.get_competencia_display(),
            'tipo_escala': self.tipo_escala,
            'status': self.status,
            'status_display': self.get_status_display(),
            'criado_por_id': self.criado_por_id,
            'criado_por_nome': self.criado_por.nome_completo if self.criado_por else None,
            'observacao': self.observacao,
            'total_distribuicoes': self.distribuicoes.count(),
            'criada_em': self.criada_em.isoformat() if self.criada_em else None,
            'atualizada_em': self.atualizada_em.isoformat() if self.atualizada_em else None,
            'publicada_em': self.publicada_em.isoformat() if self.publicada_em else None,
            'finalizada_em': self.finalizada_em.isoformat() if self.finalizada_em else None
        }
    
    def get_competencia_display(self):
        """
        Retorna a competência em formato legível
        
        Returns:
            str: Ex: "Janeiro/2025"
        """
        meses = [
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ]
        return f'{meses[self.competencia_mes - 1]}/{self.competencia_ano}'
    
    def get_status_display(self):
        """
        Retorna o status em formato legível
        
        Returns:
            str: Status amigável
        """
        status_map = {
            'RASCUNHO': 'Rascunho',
            'PUBLICADA': 'Publicada',
            'FINALIZADA': 'Finalizada',
            'CANCELADA': 'Cancelada'
        }
        return status_map.get(self.status, self.status)
    
    def get_dias_mes(self):
        """
        Retorna o número de dias no mês da competência
        
        Returns:
            int: Número de dias (28-31)
        """
        return calendar.monthrange(self.competencia_ano, self.competencia_mes)[1]
    
    def publicar(self):
        """
        Publica a escala
        """
        self.status = 'PUBLICADA'
        self.publicada_em = datetime.utcnow()
    
    def finalizar(self):
        """
        Finaliza a escala
        """
        self.status = 'FINALIZADA'
        self.finalizada_em = datetime.utcnow()
    
    def cancelar(self):
        """
        Cancela a escala
        """
        self.status = 'CANCELADA'
    
    @staticmethod
    def buscar_por_competencia(mes, ano, tipo_escala=None):
        """
        Busca escalas por competência
        
        Args:
            mes: Mês (1-12)
            ano: Ano (YYYY)
            tipo_escala: Tipo de escala (opcional)
            
        Returns:
            Query de escalas
        """
        query = Escala.query.filter_by(competencia_mes=mes, competencia_ano=ano)
        if tipo_escala:
            query = query.filter_by(tipo_escala=tipo_escala)
        return query
    
    @staticmethod
    def listar_por_status(status):
        """
        Lista escalas por status
        
        Args:
            status: Status da escala
            
        Returns:
            Query de escalas
        """
        return Escala.query.filter_by(status=status).order_by(
            Escala.competencia_ano.desc(),
            Escala.competencia_mes.desc()
        )
    
    def get_servidores_escalados(self):
        """
        Retorna lista de servidores únicos escalados nesta escala
        
        Returns:
            list: Lista de objetos Servidor
        """
        from models.servidor import Servidor
        
        servidor_ids = db.session.query(db.distinct(self.distribuicoes.c.servidor_id)).all()
        servidor_ids = [id[0] for id in servidor_ids]
        
        return Servidor.query.filter(Servidor.id.in_(servidor_ids)).all()
    
    def get_distribuicao_por_dia(self, dia):
        """
        Retorna as distribuições de um dia específico
        
        Args:
            dia: Dia do mês (1-31)
            
        Returns:
            list: Lista de EscalaDistribuicao
        """
        return self.distribuicoes.filter_by(dia_mes=dia).all()