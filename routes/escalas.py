"""
Rotas de criação e gestão de escalas
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, current_app
from flask_login import login_required, current_user
from models.escala import Escala
from models.servidor import Servidor
from models.escala_distribuicao import EscalaDistribuicao
from models.auditoria import Auditoria
from services.validacoes import Validacoes
from services.distribuicao_automatica import DistribuicaoAutomatica
from services.excel_escala_3_grupos import gerar_planilha_escala_3_grupos
from services.excel_calendario_visual import gerar_planilha_calendario_visual
from utils.database import db
from datetime import datetime
import calendar

escalas_bp = Blueprint('escalas', __name__)


@escalas_bp.route('/')
@login_required
def lista():
    """
    Lista todas as escalas
    """
    # Filtros
    mes = request.args.get('mes', '', type=int)
    ano = request.args.get('ano', '', type=int)
    status = request.args.get('status', '')
    
    # Query base
    query = Escala.query
    
    # Aplicar filtros
    if mes:
        query = query.filter_by(competencia_mes=mes)
    if ano:
        query = query.filter_by(competencia_ano=ano)
    if status:
        query = query.filter_by(status=status)
    
    # Ordenar
    escalas = query.order_by(
        Escala.competencia_ano.desc(),
        Escala.competencia_mes.desc()
    ).all()
    
    return render_template('escalas/lista.html', escalas=escalas)


@escalas_bp.route('/criar/passo1', methods=['GET', 'POST'])
@login_required
def criar_passo1():
    """
    Passo 1: Selecionar tipo de escala e competência
    """
    if request.method == 'POST':
        tipo_escala = request.form.get('tipo_escala', '')
        mes = request.form.get('mes', type=int)
        ano = request.form.get('ano', type=int)
        
        # Validações
        valido, msg = Validacoes.validar_tipo_escala(tipo_escala)
        if not valido:
            flash(msg, 'danger')
            return render_template('escalas/criar_passo1.html')
        
        valido, msg = Validacoes.validar_competencia(mes, ano)
        if not valido:
            flash(msg, 'danger')
            return render_template('escalas/criar_passo1.html')
        
        # Verificar se já existe escala para esta competência
        existe = Escala.buscar_por_competencia(mes, ano, tipo_escala).first()
        if existe:
            flash(f'Já existe uma escala {tipo_escala} para {mes:02d}/{ano}', 'warning')
            return redirect(url_for('escalas.visualizar', id=existe.id))
        
        # Criar escala em rascunho
        escala = Escala(
            competencia_mes=mes,
            competencia_ano=ano,
            tipo_escala=tipo_escala,
            status='RASCUNHO',
            criado_por_id=current_user.id
        )
        
        db.session.add(escala)
        db.session.commit()
        
        # Registrar auditoria
        Auditoria.registrar(
            usuario_id=current_user.id,
            acao='CREATE',
            tabela='escalas',
            registro_id=escala.id,
            dados_depois=escala.to_dict(),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.commit()
        
        flash('Escala criada! Agora selecione os servidores.', 'success')
        return redirect(url_for('escalas.criar_passo2', id=escala.id))
    
    # GET
    return render_template('escalas/criar_passo1.html')


@escalas_bp.route('/criar/passo2/<int:id>', methods=['GET', 'POST'])
@login_required
def criar_passo2(id):
    """
    Passo 2: Selecionar servidores e modo de distribuição
    """
    escala = Escala.query.get_or_404(id)
    
    # Validar se pode editar
    valido, msg = Validacoes.validar_pode_editar_escala(escala)
    if not valido:
        flash(msg, 'danger')
        return redirect(url_for('escalas.visualizar', id=id))
    
    if request.method == 'POST':
        servidores_ids = request.form.getlist('servidores_ids', type=int)
        modo_distribuicao = request.form.get('modo_distribuicao', 'rodizio')
        
        if not servidores_ids:
            flash('Selecione pelo menos um servidor', 'danger')
            # Buscar servidores para reexibir o formulário
            if escala.tipo_escala == 'GERAL':
                servidores = Servidor.listar_por_tipo_grupo('GERAL').all()
            else:  # SAUDE
                servidores_17h = Servidor.listar_por_tipo_grupo('SAUDE_17H').all()
                servidores_1730 = Servidor.listar_por_tipo_grupo('SAUDE_17H30').all()
                servidores = servidores_17h + servidores_1730
            
            return render_template('escalas/criar_passo2.html', 
                                 escala=escala, 
                                 servidores=servidores)
        
        # Distribuir automaticamente
        DistribuicaoAutomatica.redistribuir(
            escala.id,
            servidores_ids,
            escala.competencia_mes,
            escala.competencia_ano,
            modo=modo_distribuicao
        )
        
        db.session.commit()
        
        flash('Distribuição realizada com sucesso!', 'success')
        return redirect(url_for('escalas.criar_passo3', id=escala.id))
    
    # GET - Buscar servidores disponíveis
    if escala.tipo_escala == 'GERAL':
        servidores = Servidor.listar_por_tipo_grupo('GERAL').all()
    else:  # SAUDE
        servidores_17h = Servidor.listar_por_tipo_grupo('SAUDE_17H').all()
        servidores_1730 = Servidor.listar_por_tipo_grupo('SAUDE_17H30').all()
        servidores = servidores_17h + servidores_1730
    
    return render_template('escalas/criar_passo2.html', 
                         escala=escala, 
                         servidores=servidores)


@escalas_bp.route('/criar/passo3/<int:id>', methods=['GET', 'POST'])
@login_required
def criar_passo3(id):
    """
    Passo 3: Revisar e ajustar distribuição manualmente
    """
    escala = Escala.query.get_or_404(id)
    
    # Validar se pode editar
    valido, msg = Validacoes.validar_pode_editar_escala(escala)
    if not valido:
        flash(msg, 'danger')
        return redirect(url_for('escalas.visualizar', id=id))
    
    if request.method == 'POST':
        # Processar ajustes manuais (via AJAX normalmente)
        # Por enquanto, só marcar como publicada
        
        escala.publicar()
        db.session.commit()
        
        flash('Escala publicada com sucesso!', 'success')
        return redirect(url_for('escalas.visualizar', id=escala.id))
    
    # GET - Buscar distribuição atual
    dias_mes = calendar.monthrange(escala.competencia_ano, escala.competencia_mes)[1]
    
    # Organizar distribuição por dia
    distribuicao_por_dia = {}
    for dia in range(1, dias_mes + 1):
        distribuicoes = escala.get_distribuicao_por_dia(dia)
        distribuicao_por_dia[dia] = distribuicoes
    
    # Buscar servidores disponíveis para ajustes
    if escala.tipo_escala == 'GERAL':
        servidores = Servidor.listar_por_tipo_grupo('GERAL').all()
    else:
        servidores_17h = Servidor.listar_por_tipo_grupo('SAUDE_17H').all()
        servidores_1730 = Servidor.listar_por_tipo_grupo('SAUDE_17H30').all()
        servidores = servidores_17h + servidores_1730
    
    return render_template('escalas/criar_passo3.html',
                         escala=escala,
                         distribuicao_por_dia=distribuicao_por_dia,
                         dias_mes=dias_mes,
                         servidores=servidores)


@escalas_bp.route('/visualizar/<int:id>')
@login_required
def visualizar(id):
    """
    Visualizar escala existente
    """
    escala = Escala.query.get_or_404(id)
    
    # Buscar distribuição
    dias_mes = escala.get_dias_mes()
    
    distribuicao_por_dia = {}
    for dia in range(1, dias_mes + 1):
        distribuicoes = escala.get_distribuicao_por_dia(dia)
        distribuicao_por_dia[dia] = distribuicoes
    
    # Estatísticas
    estatisticas = DistribuicaoAutomatica.obter_estatisticas_distribuicao(escala.id)
    
    return render_template('escalas/visualizar.html',
                         escala=escala,
                         distribuicao_por_dia=distribuicao_por_dia,
                         dias_mes=dias_mes,
                         estatisticas=estatisticas)


@escalas_bp.route('/gerar-excel-3-grupos/<int:id>')
@login_required
def gerar_excel_3_grupos(id):
    """
    Gerar planilha de escala com 3 grupos
    """
    escala = Escala.query.get_or_404(id)
    
    try:
        # Gerar planilha
        caminho = gerar_planilha_escala_3_grupos(
            escala.id,
            escala.competencia_mes,
            escala.competencia_ano,
            current_app.config['PREFEITURA_NOME'],
            current_app.config['PREFEITURA_CIDADE']
        )
        
        # Registrar auditoria
        Auditoria.registrar(
            usuario_id=current_user.id,
            acao='EXPORT',
            tabela='escalas',
            registro_id=escala.id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.commit()
        
        # Enviar arquivo
        return send_file(
            caminho,
            as_attachment=True,
            download_name=f'Escala_3_Grupos_{escala.competencia_mes:02d}_{escala.competencia_ano}.xlsx'
        )
    
    except Exception as e:
        flash(f'Erro ao gerar planilha: {str(e)}', 'danger')
        return redirect(url_for('escalas.visualizar', id=id))


@escalas_bp.route('/gerar-excel-calendario/<int:id>')
@login_required
def gerar_excel_calendario(id):
    """
    Gerar planilha de calendário visual
    """
    escala = Escala.query.get_or_404(id)
    
    # Validar se é escala GERAL
    if escala.tipo_escala != 'GERAL':
        flash('Calendário visual só está disponível para escalas do tipo GERAL', 'warning')
        return redirect(url_for('escalas.visualizar', id=id))
    
    try:
        # Gerar planilha
        caminho = gerar_planilha_calendario_visual(
            escala.id,
            escala.competencia_mes,
            escala.competencia_ano
        )
        
        # Registrar auditoria
        Auditoria.registrar(
            usuario_id=current_user.id,
            acao='EXPORT',
            tabela='escalas',
            registro_id=escala.id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.commit()
        
        # Enviar arquivo
        return send_file(
            caminho,
            as_attachment=True,
            download_name=f'Calendario_Visual_{escala.competencia_mes:02d}_{escala.competencia_ano}.xlsx'
        )
    
    except Exception as e:
        flash(f'Erro ao gerar calendário: {str(e)}', 'danger')
        return redirect(url_for('escalas.visualizar', id=id))


@escalas_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir(id):
    """
    Excluir escala
    """
    escala = Escala.query.get_or_404(id)
    
    # Validar se pode excluir
    valido, msg = Validacoes.validar_pode_excluir_escala(escala)
    if not valido:
        flash(msg, 'danger')
        return redirect(url_for('escalas.visualizar', id=id))
    
    # Guardar dados
    dados_antes = escala.to_dict()
    
    db.session.delete(escala)
    db.session.commit()
    
    # Registrar auditoria
    Auditoria.registrar(
        usuario_id=current_user.id,
        acao='DELETE',
        tabela='escalas',
        registro_id=id,
        dados_antes=dados_antes,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    db.session.commit()
    
    flash('Escala excluída com sucesso!', 'success')
    return redirect(url_for('escalas.lista'))


@escalas_bp.route('/api/atualizar-dia', methods=['POST'])
@login_required
def api_atualizar_dia():
    """
    API para atualizar distribuição de um dia (AJAX)
    """
    data = request.get_json()
    
    escala_id = data.get('escala_id')
    dia = data.get('dia')
    servidor_id = data.get('servidor_id')
    acao = data.get('acao')  # 'adicionar' ou 'remover'
    
    escala = Escala.query.get(escala_id)
    if not escala:
        return jsonify({'success': False, 'message': 'Escala não encontrada'}), 404
    
    # Validar se pode editar
    valido, msg = Validacoes.validar_pode_editar_escala(escala)
    if not valido:
        return jsonify({'success': False, 'message': msg}), 400
    
    if acao == 'adicionar':
        # Verificar conflito
        if EscalaDistribuicao.verificar_conflito(servidor_id, escala_id, dia):
            return jsonify({'success': False, 'message': 'Servidor já está neste dia'}), 400
        
        # Adicionar distribuição
        dist = EscalaDistribuicao(
            escala_id=escala_id,
            servidor_id=servidor_id,
            dia_mes=dia
        )
        db.session.add(dist)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Distribuição adicionada'})
    
    elif acao == 'remover':
        # Remover distribuição
        dist = EscalaDistribuicao.query.filter_by(
            escala_id=escala_id,
            servidor_id=servidor_id,
            dia_mes=dia
        ).first()
        
        if dist:
            db.session.delete(dist)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Distribuição removida'})
        
        return jsonify({'success': False, 'message': 'Distribuição não encontrada'}), 404
    
    return jsonify({'success': False, 'message': 'Ação inválida'}), 400