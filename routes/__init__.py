"""
Inicialização das rotas
"""

from flask import Blueprint

# Importar blueprints
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.secretarias import secretarias_bp
from routes.servidores import servidores_bp
from routes.escalas import escalas_bp
from routes.plantoes import plantoes_bp
from routes.relatorios import relatorios_bp


def register_blueprints(app):
    """
    Registra todos os blueprints na aplicação Flask
    
    Args:
        app: Instância da aplicação Flask
    """
    # Registrar blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(secretarias_bp, url_prefix='/secretarias')
    app.register_blueprint(servidores_bp, url_prefix='/servidores')
    app.register_blueprint(escalas_bp, url_prefix='/escalas')
    app.register_blueprint(plantoes_bp, url_prefix='/plantoes')
    app.register_blueprint(relatorios_bp, url_prefix='/relatorios')


__all__ = [
    'register_blueprints',
    'auth_bp',
    'dashboard_bp',
    'secretarias_bp',
    'servidores_bp',
    'escalas_bp',
    'plantoes_bp',
    'relatorios_bp'
]