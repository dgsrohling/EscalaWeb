"""
Configurações do sistema EscalaWeb
"""

import os
from datetime import timedelta
from pathlib import Path

# Diretório base do projeto
BASE_DIR = Path(__file__).parent.absolute()


class Config:
    """Configuração base"""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Banco de Dados
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{BASE_DIR / "database" / "escalaweb.db"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # True para ver queries SQL no console
    
    # Sessão
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    SESSION_COOKIE_SECURE = False  # True em produção com HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hora
    
    # Upload e Export
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    EXPORT_FOLDER = BASE_DIR / 'exports'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
    
    # Logs
    LOG_FOLDER = BASE_DIR / 'logs'
    LOG_FILE = LOG_FOLDER / 'escalaweb.log'
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Paginação
    ITEMS_PER_PAGE = int(os.environ.get('ITEMS_PER_PAGE', 20))
    
    # Timezone
    TIMEZONE = os.environ.get('TIMEZONE', 'America/Sao_Paulo')
    
    # Prefeitura (Personalização)
    PREFEITURA_NOME = os.environ.get('PREFEITURA_NOME', 'Prefeitura Municipal')
    PREFEITURA_CIDADE = os.environ.get('PREFEITURA_CIDADE', 'Sua Cidade')
    PREFEITURA_UF = os.environ.get('PREFEITURA_UF', 'SP')
    
    # Email (para notificações futuras)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Admin padrão (primeiro acesso)
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@prefeitura.gov.br')
    
    # Tipos de grupos de escala
    TIPOS_GRUPO = {
        'GERAL': 'GERAL',
        'SAUDE_17H': 'SAÚDE 17h',
        'SAUDE_17H30': 'SAÚDE 17h30'
    }
    
    # Horários de sobreaviso
    HORARIOS_SOBREAVISO = {
        'GERAL': {'inicio': '17:00', 'fim': '08:00'},
        'SAUDE_17H': {'inicio': '17:00', 'fim': '08:00'},
        'SAUDE_17H30': {'inicio': '17:30', 'fim': '08:00'}
    }
    
    # Horário de adicional noturno (legislação trabalhista)
    HORARIO_NOTURNO_INICIO = '22:00'
    HORARIO_NOTURNO_FIM = '05:00'
    
    # Status de escalas
    STATUS_ESCALA = {
        'RASCUNHO': 'Rascunho',
        'PUBLICADA': 'Publicada',
        'FINALIZADA': 'Finalizada',
        'CANCELADA': 'Cancelada'
    }
    
    # Tipos de plantão
    TIPOS_PLANTAO = {
        'NORMAL': 'Normal',
        'FERIADO': 'Feriado',
        'FINAL_SEMANA': 'Final de Semana'
    }
    
    @staticmethod
    def init_app(app):
        """Inicializa configurações específicas da aplicação"""
        
        # Criar diretórios necessários
        folders = [
            Config.UPLOAD_FOLDER,
            Config.EXPORT_FOLDER,
            Config.LOG_FOLDER,
            BASE_DIR / 'database'
        ]
        
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)
        
        # Configurar logging
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug and not app.testing:
            # Log em arquivo
            file_handler = RotatingFileHandler(
                Config.LOG_FILE,
                maxBytes=10240000,  # 10MB
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(getattr(logging, Config.LOG_LEVEL))
            app.logger.addHandler(file_handler)
        
        app.logger.setLevel(getattr(logging, Config.LOG_LEVEL))
        app.logger.info('EscalaWeb startup')


class DevelopmentConfig(Config):
    """Configuração de Desenvolvimento"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True  # Mostra queries SQL


class ProductionConfig(Config):
    """Configuração de Produção"""
    DEBUG = False
    TESTING = False
    
    # Em produção, SECRET_KEY deve vir obrigatoriamente do ambiente
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Garantir que SECRET_KEY está definida
        assert os.environ.get('SECRET_KEY'), \
            'SECRET_KEY must be set in production!'
        
        # Configurações de segurança para produção
        app.config['SESSION_COOKIE_SECURE'] = True
        
        # Log para syslog em produção (opcional)
        import logging
        from logging.handlers import SysLogHandler
        
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


class TestingConfig(Config):
    """Configuração de Testes"""
    TESTING = True
    DEBUG = True
    
    # Usar banco de dados em memória para testes
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Desabilitar CSRF em testes
    WTF_CSRF_ENABLED = False


# Dicionário de configurações
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Retorna a configuração baseada na variável de ambiente FLASK_ENV"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])