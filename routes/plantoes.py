"""
Rotas de registro de plantões
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from models.servidor import Servidor
from models.plantao_realizado import PlantaoRealizado
from models.auditoria import Auditoria
from services.validacoes import Validacoes
from services.calculador_horas import CalculadorHoras
from services.excel_plantao_individual import gerar_planilha_plantao_individual
from utils.database import db
from datetime import datetime, time
import calendar

plantoes_bp = Blueprint('plantoes', __name__)


@plantoes_bp.route('/registrar/passo1', methods=['GET', 'POST'])
@login_required
def registrar_passo1():
    """
    Passo 1: Selecionar servidor e competência
    """
    if request.method == 'POST':
        servidor_id = request.form.get('servidor_id', type=int)
        mes = request.form.get('mes', type=int)
        ano = request.form.get('ano', type=int)
        
        # Validações
        if not servidor_id:
            flash('Selecione um servidor', 'danger')
            servidores = Servidor.listar_ativos().all()
            return render_template('plantoes/registrar_passo1.html', servidores=servidores)
        
        valido, msg = Validacoes.validar_competencia(mes, ano)
        if not valido:
            flash(msg, 'danger')
            servidores = Servidor.listar_ativos().all()
            return render_template('plantoes/registrar_passo1.html', servidores=servidores)
        
        # Verificar se servidor existe
        servidor = Servidor.query.get(servidor_id)
        if not servidor:
            flash('Servidor não encontrado', 'danger')
            servidores = Servidor.listar_ativos().all()
            return render_template('plantoes/registrar_passo1.html', servidores=servidores)
        
        return redirect(url_for('plantoes.registrar_passo2',
                              servidor_id=servidor_id,
                              mes=mes,
                              ano=ano))
    
    # GET
    servidores = Servidor.listar_ativos().all()
    hoje = datetime.now()
    
    return render_template('plantoes/registrar_passo1.html',
                         servidores=servidores,
                         mes_default=hoje.month,
                         ano_default=hoje.year)


@plantoes_bp.route('/registrar/passo2')
@login_required
def registrar_passo2():
    """
    Passo 2: Marcar dias trabalhados
    """
    servidor_id = request.args.get('servidor_id', type=int)
    mes = request.args.get('mes', type=int)
    ano = request.args.get('ano', type=int)
    
    # Validações
    if not servidor_id or not mes or not ano:
        flash('Dados incompletos', 'danger')
        return redirect(url_for('plantoes.registrar_passo1'))
    
    servidor = Servidor.query.get_or_404(servidor_id)
    
    # Buscar plantões já registrados
    plantoes = PlantaoRealizado.buscar_por_servidor_e_competencia(
        servidor_id, mes, ano
    )
    
    # Organizar por dia
    plantoes_dict = {p.dia_mes: p for p in plantoes}
    
    # Obter número de dias no mês
    dias_mes = calendar.monthrange(ano, mes)[1]
    
    # Obter horários padrão do grupo
    horarios = servidor.get_horario_sobreaviso()
    
    return render_template('plantoes/registrar_passo2.html',
                         servidor=servidor,
                         mes=mes,
                         ano=ano,
                         plantoes_dict=plantoes_dict,
                         dias_mes=dias_mes,
                         horarios=horarios)


@plantoes_bp.route('/registrar/salvar', methods=['POST'])
@login_required
def salvar():
    """
    Salvar plantões marcados
    """
    servidor_id = request.form.get('servidor_id', type=int)
    mes = request.form.get('mes', type=int)
    ano = request.form.get('ano', type=int)
    
    if not servidor_id or not mes or not ano:
        flash('Dados incompletos', 'danger')
        return redirect(url_for('plantoes.registrar_passo1'))
    
    servidor = Servidor.query.get_or_404(servidor_id)
    dias_mes = calendar.monthrange(ano, mes)[1]
    
    # Processar cada dia
    for dia in range(1, dias_mes + 1):
        # Verificar se dia foi marcado
        dia_marcado = request.form.get(f'dia[{dia}]') == 'on'
        
        # Obter horários
        hora_inicio_str = request.form.get(f'hora_inicio[{dia}]', '').strip()
        hora_fim_str = request.form.get(f'hora_fim[{dia}]', '').strip()
        
        # Verificar se plantão já existe
        plantao_existente = PlantaoRealizado.query.filter_by(
            servidor_id=servidor_id,
            competencia_mes=mes,
            competencia_ano=ano,
            dia_mes=dia
        ).first()
        
        if dia_marcado and hora_inicio_str and hora_fim_str:
            # Validar horários
            valido, msg = Validacoes.validar_horario(hora_inicio_str)
            if not valido:
                flash(f'Dia {dia}: {msg}', 'warning')
                continue
            
            valido, msg = Validacoes.validar_horario(hora_fim_str)
            if not valido:
                flash(f'Dia {dia}: {msg}', 'warning')
                continue
            
            # Converter para time
            h_i, m_i = map(int, hora_inicio_str.split(':'))
            hora_inicio = time(h_i, m_i)
            
            h_f, m_f = map(int, hora_fim_str.split(':'))
            hora_fim = time(h_f, m_f)
            
            # Calcular horas
            horas_trabalhadas = CalculadorHoras.calcular_horas_trabalhadas(hora_inicio, hora_fim)
            adicional_noturno = CalculadorHoras.calcular_adicional_noturno(hora_inicio, hora_fim)
            
            if plantao_existente:
                # Atualizar
                plantao_existente.hora_inicio = hora_inicio
                plantao_existente.hora_fim = hora_fim
                plantao_existente.horas_trabalhadas = horas_trabalhadas
                plantao_existente.adicional_noturno = adicional_noturno
            else:
                # Criar novo
                plantao = PlantaoRealizado(
                    servidor_id=servidor_id,
                    competencia_mes=mes,
                    competencia_ano=ano,
                    dia_mes=dia,
                    hora_inicio=hora_inicio,
                    hora_fim=hora_fim,
                    horas_trabalhadas=horas_trabalhadas,
                    adicional_noturno=adicional_noturno,
                    tipo_plantao='NORMAL'
                )
                db.session.add(plantao)
        
        elif plantao_existente:
            # Dia desmarcado - remover plantão
            db.session.delete(plantao_existente)
    
    db.session.commit()
    
    # Registrar auditoria
    Auditoria.registrar(
        usuario_id=current_user.id,
        acao='UPDATE',
        tabela='plantoes_realizados',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    db.session.commit()
    
    flash('Plantões salvos com sucesso!', 'success')
    return redirect(url_for('plantoes.resumo',
                          servidor_id=servidor_id,
                          mes=mes,
                          ano=ano))


@plantoes_bp.route('/resumo')
@login_required
def resumo():
    """
    Resumo dos plantões do servidor no mês
    """
    servidor_id = request.args.get('servidor_id', type=int)
    mes = request.args.get('mes', type=int)
    ano = request.args.get('ano', type=int)
    
    if not servidor_id or not mes or not ano:
        flash('Dados incompletos', 'danger')
        return redirect(url_for('plantoes.registrar_passo1'))
    
    servidor = Servidor.query.get_or_404(servidor_id)
    
    # Buscar plantões
    plantoes = PlantaoRealizado.buscar_por_servidor_e_competencia(
        servidor_id, mes, ano
    )
    
    # Calcular totais
    totais = PlantaoRealizado.total_horas_servidor_mes(servidor_id, mes, ano)
    
    return render_template('plantoes/resumo.html',
                         servidor=servidor,
                         mes=mes,
                         ano=ano,
                         plantoes=plantoes,
                         totais=totais)


@plantoes_bp.route('/gerar-planilha')
@login_required
def gerar_planilha():
    """
    Gerar planilha individual de plantões
    """
    servidor_id = request.args.get('servidor_id', type=int)
    mes = request.args.get('mes', type=int)
    ano = request.args.get('ano', type=int)
    
    if not servidor_id or not mes or not ano:
        flash('Dados incompletos', 'danger')
        return redirect(url_for('plantoes.registrar_passo1'))
    
    try:
        # Gerar planilha
        caminho = gerar_planilha_plantao_individual(
            servidor_id,
            mes,
            ano
        )
        
        # Registrar auditoria
        Auditoria.registrar(
            usuario_id=current_user.id,
            acao='EXPORT',
            tabela='plantoes_realizados',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.commit()
        
        # Enviar arquivo
        servidor = Servidor.query.get(servidor_id)
        nome_arquivo = f'{servidor.nome_completo}_{servidor.matricula}_{mes:02d}-{ano}.xlsx'
        
        return send_file(
            caminho,
            as_attachment=True,
            download_name=nome_arquivo
        )
    
    except Exception as e:
        flash(f'Erro ao gerar planilha: {str(e)}', 'danger')
        return redirect(url_for('plantoes.resumo',
                              servidor_id=servidor_id,
                              mes=mes,
                              ano=ano))


@plantoes_bp.route('/lista')
@login_required
def lista():
    """
    Lista todos os plantões com filtros
    """
    # Filtros
    servidor_id = request.args.get('servidor_id', type=int)
    mes = request.args.get('mes', type=int)
    ano = request.args.get('ano', type=int)
    
    # Query base
    query = PlantaoRealizado.query
    
    # Aplicar filtros
    if servidor_id:
        query = query.filter_by(servidor_id=servidor_id)
    if mes:
        query = query.filter_by(competencia_mes=mes)
    if ano:
        query = query.filter_by(competencia_ano=ano)
    
    # Ordenar
    plantoes = query.order_by(
        PlantaoRealizado.competencia_ano.desc(),
        PlantaoRealizado.competencia_mes.desc(),
        PlantaoRealizado.dia_mes.desc()
    ).all()
    
    # Buscar servidores para filtro
    servidores = Servidor.listar_ativos().all()
    
    return render_template('plantoes/lista.html',
                         plantoes=plantoes,
                         servidores=servidores,
                         servidor_id=servidor_id,
                         mes=mes,
                         ano=ano)