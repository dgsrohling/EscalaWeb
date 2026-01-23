"""
Rotas do dashboard
"""

from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from datetime import datetime
from services.estatisticas import Estatisticas
from models.servidor import Servidor
from models.escala import Escala

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def index():
    """
    Dashboard principal
    """
    # Obter mês/ano atual ou filtrado
    hoje = datetime.now()
    mes = request.args.get('mes', hoje.month, type=int)
    ano = request.args.get('ano', hoje.year, type=int)
    
    # Estatísticas gerais
    stats_gerais = Estatisticas.estatisticas_gerais(mes, ano)
    
    # Top 10 plantonistas
    top_plantonistas = Estatisticas.top_plantonistas(mes, ano, limite=10)
    
    # Distribuição por grupo
    distribuicao_grupos = Estatisticas.distribuicao_por_grupo(mes, ano)
    
    # Servidores mais escalados
    mais_escalados = Estatisticas.servidores_mais_escalados(mes, ano, limite=10)
    
    # Taxa de ocupação
    taxa_ocupacao = Estatisticas.taxa_ocupacao_mes(mes, ano)
    
    # Dados para gráfico comparativo mensal
    comparativo = Estatisticas.comparativo_mensal(ano)
    
    # Escalas do mês
    escalas_mes = Escala.buscar_por_competencia(mes, ano).all()
    
    return render_template(
        'dashboard/index.html',
        mes=mes,
        ano=ano,
        stats_gerais=stats_gerais,
        top_plantonistas=top_plantonistas,
        distribuicao_grupos=distribuicao_grupos,
        mais_escalados=mais_escalados,
        taxa_ocupacao=taxa_ocupacao,
        comparativo=comparativo,
        escalas_mes=escalas_mes,
        hoje=hoje
    )


@dashboard_bp.route('/dashboard/servidor/<int:servidor_id>')
@login_required
def detalhes_servidor(servidor_id):
    """
    Detalhes de um servidor específico
    """
    hoje = datetime.now()
    mes = request.args.get('mes', hoje.month, type=int)
    ano = request.args.get('ano', hoje.year, type=int)
    
    # Buscar resumo do servidor
    resumo = Estatisticas.resumo_servidor(servidor_id, mes, ano)
    
    if not resumo:
        flash('Servidor não encontrado', 'danger')
        return redirect(url_for('dashboard.index'))
    
    return render_template(
        'dashboard/servidor_detalhes.html',
        resumo=resumo,
        mes=mes,
        ano=ano
    )