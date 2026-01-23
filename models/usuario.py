"""
Modelo de Usuário
"""

from datetime import datetime
from flask_login import UserMixin
from flask_bcrypt import generate_password_hash, check_password_hash
from utils.database import db


class Usuario(UserMixin, db.Model):
    """
    Modelo de usuário do sistema
    
    Attributes:
        id: ID único do usuário
        username: Nome de usuário para login (único)
        password_hash: Senha criptografada
        nome_completo: Nome completo do usuário
        email: Email do usuário
        ativo: Status do usuário (True/False)
        criado_em: Data e hora de criação
        atualizado_em: Data e hora da última atualização
    """
    
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nome_completo = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relacionamentos
    escalas_criadas = db.relationship('Escala', back_populates='criado_por', lazy='dynamic')
    auditorias = db.relationship('Auditoria', back_populates='usuario', lazy='dynamic')
    
    def __repr__(self):
        return f'<Usuario {self.username}>'
    
    def set_password(self, password):
        """
        Define a senha do usuário (criptografada)
        
        Args:
            password: Senha em texto plano
        """
        self.password_hash = generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """
        Verifica se a senha está correta
        
        Args:
            password: Senha em texto plano para verificar
            
        Returns:
            bool: True se a senha está correta, False caso contrário
        """
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """
        Converte o usuário para dicionário
        
        Returns:
            dict: Dados do usuário
        """
        return {
            'id': self.id,
            'username': self.username,
            'nome_completo': self.nome_completo,
            'email': self.email,
            'ativo': self.ativo,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
        }
    
    @staticmethod
    def buscar_por_username(username):
        """
        Busca usuário por username
        
        Args:
            username: Nome de usuário
            
        Returns:
            Usuario ou None
        """
        return Usuario.query.filter_by(username=username).first()
    
    @staticmethod
    def buscar_por_email(email):
        """
        Busca usuário por email
        
        Args:
            email: Email do usuário
            
        Returns:
            Usuario ou None
        """
        return Usuario.query.filter_by(email=email).first()
    
    @property
    def is_active(self):
        """Propriedade necessária para Flask-Login"""
        return self.ativo