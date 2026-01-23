"""
Modelo de Distribuição de Escala
"""

from datetime import datetime
from utils.database import db


class EscalaDistribuicao(db.Model):
    """
    Modelo de Distribuição de Escala (Servidor por Dia)
    
    Representa a alocação de um servidor em um dia específico da escala
    
    Attributes:
        id: ID único da distribuição
        escala_id: ID da escala
        servidor_id: ID do servidor
        dia_mes: Dia do mês (1-31)
        confirmado: Se o servidor confirmou a escala
        observacao: Observações sobre esta distribuição específica
        criada_em: Data e hora de criação
    """
    
    __tablename__ = 'escala_distribuicao'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relacionamentos
    escala_id = db.Column(db.Integer, db.ForeignKey('escalas.id'), nullable=False)
    servidor_id = db.Column(db.Integer, db.ForeignKey('servidores.id'), nullable=False)
    
    # Dia do mês
    dia_mes = db.Column(db.Integer, nullable=False)  # 1-31
    
    # Confirmação
    confirmado = db.Column(db.Boolean, default=False, nullable=False)
    
    # Observações
    observacao = db.Column(db.String(500))
    
    # Timestamp
    criada_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relacionamentos
    escala = db.relationship('Escala', back_populates='distribuicoes')
    servidor = db.relationship('Servidor', back_populates='distribuicoes')
    
    # Índice composto para evitar duplicatas e busca rápida
    __table_args__ = (
        db.UniqueConstraint('escala_id', 'servidor_id', 'dia_mes', name='uq_escala_servidor_dia'),
        db.Index('idx_escala_dia', 'escala_id', 'dia_mes'),
    )
    
    def __repr__(self):
        return f'<EscalaDistribuicao Escala={self.escala_id} Servidor={self.servidor_id} Dia={self.dia_mes}>'
    
    def to_dict(self):
        """
        Converte a distribuição para dicionário
        
        Returns:
            dict: Dados da distribuição
        """
        return {
            'id': self.id,
            'escala_id': self.escala_id,
            'servidor_id': self.servidor_id,
            'servidor_nome': self.servidor.nome_completo if self.servidor else None,
            'servidor_matricula': self.servidor.matricula if self.servidor else None,
            'dia_mes': self.dia_mes,
            'confirmado': self.confirmado,
            'observacao': self.observacao,
            'criada_em': self.criada_em.isoformat() if self.criada_em else None
        }
    
    def confirmar(self):
        """
        Confirma a distribuição
        """
        self.confirmado = True
    
    def desconfirmar(self):
        """
        Remove a confirmação da distribuição
        """
        self.confirmado = False
    
    @staticmethod
    def buscar_por_escala_e_dia(escala_id, dia_mes):
        """
        Busca distribuições de uma escala em um dia específico
        
        Args:
            escala_id: ID da escala
            dia_mes: Dia do mês (1-31)
            
        Returns:
            list: Lista de EscalaDistribuicao
        """
        return EscalaDistribuicao.query.filter_by(
            escala_id=escala_id,
            dia_mes=dia_mes
        ).all()
    
    @staticmethod
    def buscar_por_servidor_e_competencia(servidor_id, mes, ano):
        """
        Busca todas as distribuições de um servidor em uma competência
        
        Args:
            servidor_id: ID do servidor
            mes: Mês (1-12)
            ano: Ano (YYYY)
            
        Returns:
            list: Lista de EscalaDistribuicao
        """
        from models.escala import Escala
        
        return db.session.query(EscalaDistribuicao).join(Escala).filter(
            EscalaDistribuicao.servidor_id == servidor_id,
            Escala.competencia_mes == mes,
            Escala.competencia_ano == ano
        ).order_by(EscalaDistribuicao.dia_mes).all()
    
    @staticmethod
    def verificar_conflito(servidor_id, escala_id, dia_mes):
        """
        Verifica se já existe distribuição para o servidor neste dia
        
        Args:
            servidor_id: ID do servidor
            escala_id: ID da escala
            dia_mes: Dia do mês
            
        Returns:
            bool: True se existe conflito
        """
        return EscalaDistribuicao.query.filter_by(
            servidor_id=servidor_id,
            escala_id=escala_id,
            dia_mes=dia_mes
        ).first() is not None
    
    @staticmethod
    def remover_servidor_da_escala(escala_id, servidor_id):
        """
        Remove todas as distribuições de um servidor de uma escala
        
        Args:
            escala_id: ID da escala
            servidor_id: ID do servidor
            
        Returns:
            int: Número de registros removidos
        """
        distribuicoes = EscalaDistribuicao.query.filter_by(
            escala_id=escala_id,
            servidor_id=servidor_id
        ).all()
        
        count = len(distribuicoes)
        for dist in distribuicoes:
            db.session.delete(dist)
        
        return count