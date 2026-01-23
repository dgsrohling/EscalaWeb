"""
Rotas de relatórios e exportações
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models.servidor import Servidor
from models.escala import Escala
from models.plantao_realizado import PlantaoRealizado
from services.estatisticas import Estatisticas
from datetime import datetime

relatorios_bp = Blueprint('relatorios', __name__)


@relatorios_bp.route('/')
@login_required
def index():
    """
    Página inicial de relatórios
    """
    hoje = datetime.now()
    
    return render_template('relatorios/index.html',
                         mes_atual=hoje.month,
                         ano_atual=hoje.year)


@relatorios_bp.route('/estatisticas')
@login_required
def estatisticas():
    """
    Relatório de estatísticas gerais
    """
    mes = request.args.get('mes', type=int)
    ano = request.args.get('ano', type=int)
    
    # Estatísticas gerais
    stats = Estatisticas.estatisticas_gerais(mes, ano)
    
    # Top plantonistas
    top_plantonistas = Estatisticas.top_plantonistas(mes, ano, limite=10)
    
    # Distribuição por grupo
    distribuicao = Estatisticas.distribuicao_por_grupo(mes, ano)
    
    # Servidores mais escalados
    mais_escalados = []
    if mes and ano:
        mais_escalados = Estatisticas.servidores_mais_escalados(mes, ano, limite=10)
    
    return render_template('relatorios/estatisticas.html',
                         mes=mes,
                         ano=ano,
                         stats=stats,
                         top_plantonistas=top_plantonistas,
                         distribuicao=distribuicao,
                         mais_escalados=mais_escalados)


@relatorios_bp.route('/comparativo-mensal')
@login_required
def comparativo_mensal():
    """
    Relatório comparativo mensal (gráficos)
    """
    ano = request.args.get('ano', datetime.now().year, type=int)
    
    # Dados para gráficos
    comparativo = Estatisticas.comparativo_mensal(ano)
    
    # Plantões por mês
    dados_mensais = Estatisticas.plantoes_por_mes(ano)
    
    return render_template('relatorios/comparativo_mensal.html',
                         ano=ano,
                         comparativo=comparativo,
                         dados_mensais=dados_mensais)


@relatorios_bp.route('/servidor/<int:servidor_id>')
@login_required
def servidor_detalhado(servidor_id):
    """
    Relatório detalhado de um servidor
    """
    mes = request.args.get('mes', type=int)
    ano = request.args.get('ano', type=int)
    
    if not mes or not ano:
        flash('Selecione mês e ano', 'warning')
        return redirect(url_for('relatorios.index'))
    
    # Resumo do servidor
    resumo = Estatisticas.resumo_servidor(servidor_id, mes, ano)
    
    if not resumo:
        flash('Servidor não encontrado', 'danger')
        return redirect(url_for('relatorios.index'))
    
    return render_template('relatorios/servidor_detalhado.html',
                         resumo=resumo,
                         mes=mes,
                         ano=ano)


@relatorios_bp.route('/escalas-mes')
@login_required
def escalas_mes():
    """
    Relatório de escalas do mês
    """
    mes = request.args.get('mes', type=int)
    ano = request.args.get('ano', type=int)
    
    if not mes or not ano:
        flash('Selecione mês e ano', 'warning')
        return redirect(url_for('relatorios.index'))
    
    # Buscar escalas
    escalas = Escala.buscar_por_competencia(mes, ano).all()
    
    # Estatísticas das escalas
    stats_escalas = []
    for escala in escalas:
        stats = {
            'escala': escala,
            'distribuicoes': escala.distribuicoes.count(),
            'servidores_unicos': len(escala.get_servidores_escalados())
        }
        stats_escalas.append(stats)
    
    return render_template('relatorios/escalas_mes.html',
                         mes=mes,
                         ano=ano,
                         escalas=escalas,
                         stats_escalas=stats_escalas)


@relatorios_bp.route('/plantoes-mes')
@login_required
def plantoes_mes():
    """
    Relatório de plantões do mês
    """
    mes = request.args.get('mes', type=int)
    ano = request.args.get('ano', type=int)
    
    if not mes or not ano:
        flash('Selecione mês e ano', 'warning')
        return redirect(url_for('relatorios.index'))
    
    # Buscar todos os plantões do mês
    plantoes = PlantaoRealizado.query.filter_by(
        competencia_mes=mes,
        competencia_ano=ano
    ).order_by(PlantaoRealizado.dia_mes).all()
    
    # Agrupar por servidor
    plantoes_por_servidor = {}
    for plantao in plantoes:
        if plantao.servidor_id not in plantoes_por_servidor:
            plantoes_por_servidor[plantao.servidor_id] = {
                'servidor': plantao.servidor,
                'plantoes': [],
                'total_dias': 0,
                'total_horas': 0,
                'total_noturno': 0
            }
        
        plantoes_por_servidor[plantao.servidor_id]['plantoes'].append(plantao)
        plantoes_por_servidor[plantao.servidor_id]['total_dias'] += 1
        plantoes_por_servidor[plantao.servidor_id]['total_horas'] += plantao.horas_trabalhadas or 0
        plantoes_por_servidor[plantao.servidor_id]['total_noturno'] += plantao.adicional_noturno or 0
    
    return render_template('relatorios/plantoes_mes.html',
                         mes=mes,
                         ano=ano,
                         plantoes_por_servidor=plantoes_por_servidor)


@relatorios_bp.route('/taxa-ocupacao')
@login_required
def taxa_ocupacao():
    """
    Relatório de taxa de ocupação
    """
    ano = request.args.get('ano', datetime.now().year, type=int)
    
    # Calcular taxa de ocupação para cada mês
    taxas_mensais = {}
    for mes in range(1, 13):
        taxa = Estatisticas.taxa_ocupacao_mes(mes, ano)
        taxas_mensais[mes] = taxa
    
    return render_template('relatorios/taxa_ocupacao.html',
                         ano=ano,
                         taxas_mensais=taxas_mensais)