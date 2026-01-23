"""
Modelo de Auditoria
"""

from datetime import datetime
import json
from utils.database import db


class Auditoria(db.Model):
    """
    Modelo de Auditoria (Logs do Sistema)
    
    Registra todas as ações importantes realizadas no sistema
    
    Attributes:
        id: ID único do log
        usuario_id: ID do usuário que realizou a ação
        acao: Tipo de ação (CREATE, UPDATE, DELETE, LOGIN, LOGOUT, etc.)
        tabela: Nome da tabela afetada
        registro_id: ID do registro afetado
        dados_antes: Dados antes da alteração (JSON)
        dados_depois: Dados depois da alteração (JSON)
        ip_address: Endereço IP do usuário
        user_agent: User agent do navegador
        criado_em: Data e hora da ação
    """
    
    __tablename__ = 'auditoria'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relacionamento com usuário
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    # Ação realizada
    acao = db.Column(db.String(50), nullable=False, index=True)
    # acao: 'CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'EXPORT', etc.
    
    # Entidade afetada
    tabela = db.Column(db.String(100), index=True)
    registro_id = db.Column(db.Integer)
    
    # Dados da alteração (JSON)
    dados_antes = db.Column(db.Text)  # JSON string
    dados_depois = db.Column(db.Text)  # JSON string
    
    # Informações da requisição
    ip_address = db.Column(db.String(45))  # Suporta IPv6
    user_agent = db.Column(db.String(500))
    
    # Timestamp
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relacionamentos
    usuario = db.relationship('Usuario', back_populates='auditorias')
    
    def __repr__(self):
        return f'<Auditoria {self.acao} - {self.tabela} - Usuario={self.usuario_id}>'
    
    def to_dict(self):
        """
        Converte o log de auditoria para dicionário
        
        Returns:
            dict: Dados da auditoria
        """
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'usuario_nome': self.usuario.nome_completo if self.usuario else 'Sistema',
            'acao': self.acao,
            'tabela': self.tabela,
            'registro_id': self.registro_id,
            'dados_antes': self.get_dados_antes(),
            'dados_depois': self.get_dados_depois(),
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None
        }
    
    def get_dados_antes(self):
        """
        Retorna dados_antes como dicionário
        
        Returns:
            dict ou None
        """
        if self.dados_antes:
            try:
                return json.loads(self.dados_antes)
            except:
                return None
        return None
    
    def get_dados_depois(self):
        """
        Retorna dados_depois como dicionário
        
        Returns:
            dict ou None
        """
        if self.dados_depois:
            try:
                return json.loads(self.dados_depois)
            except:
                return None
        return None
    
    @staticmethod
    def registrar(usuario_id, acao, tabela=None, registro_id=None, 
                  dados_antes=None, dados_depois=None, 
                  ip_address=None, user_agent=None):
        """
        Registra uma ação na auditoria
        
        Args:
            usuario_id: ID do usuário (None para ações do sistema)
            acao: Tipo de ação
            tabela: Nome da tabela afetada
            registro_id: ID do registro afetado
            dados_antes: Dados antes da alteração (dict)
            dados_depois: Dados depois da alteração (dict)
            ip_address: IP do usuário
            user_agent: User agent
            
        Returns:
            Auditoria: Objeto criado
        """
        auditoria = Auditoria(
            usuario_id=usuario_id,
            acao=acao,
            tabela=tabela,
            registro_id=registro_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Converter dados para JSON
        if dados_antes:
            auditoria.dados_antes = json.dumps(dados_antes, ensure_ascii=False)
        
        if dados_depois:
            auditoria.dados_depois = json.dumps(dados_depois, ensure_ascii=False)
        
        db.session.add(auditoria)
        
        return auditoria
    
    @staticmethod
    def buscar_por_usuario(usuario_id, limite=100):
        """
        Busca logs de um usuário específico
        
        Args:
            usuario_id: ID do usuário
            limite: Número máximo de registros
            
        Returns:
            list: Lista de Auditoria
        """
        return Auditoria.query.filter_by(usuario_id=usuario_id)\
            .order_by(Auditoria.criado_em.desc())\
            .limit(limite).all()
    
    @staticmethod
    def buscar_por_tabela(tabela, registro_id=None, limite=100):
        """
        Busca logs de uma tabela específica
        
        Args:
            tabela: Nome da tabela
            registro_id: ID do registro (opcional)
            limite: Número máximo de registros
            
        Returns:
            list: Lista de Auditoria
        """
        query = Auditoria.query.filter_by(tabela=tabela)
        
        if registro_id:
            query = query.filter_by(registro_id=registro_id)
        
        return query.order_by(Auditoria.criado_em.desc()).limit(limite).all()
    
    @staticmethod
    def buscar_por_acao(acao, limite=100):
        """
        Busca logs de uma ação específica
        
        Args:
            acao: Tipo de ação
            limite: Número máximo de registros
            
        Returns:
            list: Lista de Auditoria
        """
        return Auditoria.query.filter_by(acao=acao)\
            .order_by(Auditoria.criado_em.desc())\
            .limit(limite).all()
    
    @staticmethod
    def buscar_por_periodo(data_inicio, data_fim, limite=1000):
        """
        Busca logs em um período específico
        
        Args:
            data_inicio: Data de início
            data_fim: Data de fim
            limite: Número máximo de registros
            
        Returns:
            list: Lista de Auditoria
        """
        return Auditoria.query.filter(
            Auditoria.criado_em >= data_inicio,
            Auditoria.criado_em <= data_fim
        ).order_by(Auditoria.criado_em.desc()).limit(limite).all()
    
    @staticmethod
    def limpar_logs_antigos(dias=90):
        """
        Remove logs mais antigos que X dias
        
        Args:
            dias: Número de dias para manter
            
        Returns:
            int: Número de registros removidos
        """
        data_limite = datetime.utcnow() - timedelta(days=dias)
        logs_antigos = Auditoria.query.filter(Auditoria.criado_em < data_limite).all()
        
        count = len(logs_antigos)
        for log in logs_antigos:
            db.session.delete(log)
        
        return count