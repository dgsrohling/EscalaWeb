"""
Modelo de Secretaria
"""

from datetime import datetime
from utils.database import db


class Secretaria(db.Model):
    """
    Modelo de Secretaria Municipal
    
    Attributes:
        id: ID único da secretaria
        nome: Nome completo da secretaria
        sigla: Sigla da secretaria (ex: SELOG, SESAU)
        ativa: Status da secretaria (True/False)
        criada_em: Data e hora de criação
        atualizada_em: Data e hora da última atualização
    """
    
    __tablename__ = 'secretarias'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    sigla = db.Column(db.String(20), unique=True, nullable=False, index=True)
    ativa = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps
    criada_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    atualizada_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relacionamentos
    servidores = db.relationship('Servidor', back_populates='secretaria', lazy='dynamic')
    
    def __repr__(self):
        return f'<Secretaria {self.sigla}>'
    
    def to_dict(self):
        """
        Converte a secretaria para dicionário
        
        Returns:
            dict: Dados da secretaria
        """
        return {
            'id': self.id,
            'nome': self.nome,
            'sigla': self.sigla,
            'ativa': self.ativa,
            'total_servidores': self.servidores.count(),
            'criada_em': self.criada_em.isoformat() if self.criada_em else None,
            'atualizada_em': self.atualizada_em.isoformat() if self.atualizada_em else None
        }
    
    @staticmethod
    def listar_ativas():
        """
        Lista apenas secretarias ativas
        
        Returns:
            Query de secretarias ativas
        """
        return Secretaria.query.filter_by(ativa=True).order_by(Secretaria.nome)
    
    @staticmethod
    def buscar_por_sigla(sigla):
        """
        Busca secretaria por sigla
        
        Args:
            sigla: Sigla da secretaria
            
        Returns:
            Secretaria ou None
        """
        return Secretaria.query.filter_by(sigla=sigla.upper()).first()