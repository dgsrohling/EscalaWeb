"""
Inicialização dos modelos
"""

from utils.database import db

# Importar todos os modelos para que o SQLAlchemy os reconheça
from models.usuario import Usuario
from models.secretaria import Secretaria
from models.servidor import Servidor
from models.escala import Escala
from models.escala_distribuicao import EscalaDistribuicao
from models.plantao_realizado import PlantaoRealizado
from models.auditoria import Auditoria

__all__ = [
    'db',
    'Usuario',
    'Secretaria',
    'Servidor',
    'Escala',
    'EscalaDistribuicao',
    'PlantaoRealizado',
    'Auditoria'
]