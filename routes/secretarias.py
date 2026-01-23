"""
Rotas CRUD de secretarias
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.secretaria import Secretaria
from models.auditoria import Auditoria
from services.validacoes import Validacoes
from utils.database import db

secretarias_bp = Blueprint('secretarias', __name__)


@secretarias_bp.route('/')
@login_required
def lista():
    """
    Lista todas as secretarias
    """
    # Buscar todas as secretarias
    secretarias = Secretaria.query.order_by(Secretaria.nome).all()
    
    return render_template('cadastros/secretarias_lista.html', secretarias=secretarias)


@secretarias_bp.route('/nova', methods=['GET', 'POST'])
@login_required
def nova():
    """
    Criar nova secretaria
    """
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        sigla = request.form.get('sigla', '').strip().upper()
        ativa = request.form.get('ativa', 'on') == 'on'
        
        # Validações
        if not nome:
            flash('Nome é obrigatório', 'danger')
            return render_template('cadastros/secretarias_form.html')
        
        valido, msg = Validacoes.validar_sigla_secretaria(sigla)
        if not valido:
            flash(msg, 'danger')
            return render_template('cadastros/secretarias_form.html')
        
        # Verificar se sigla já existe
        existe = Secretaria.buscar_por_sigla(sigla)
        if existe:
            flash(f'Já existe uma secretaria com a sigla {sigla}', 'danger')
            return render_template('cadastros/secretarias_form.html')
        
        # Criar secretaria
        secretaria = Secretaria(
            nome=nome,
            sigla=sigla,
            ativa=ativa
        )
        
        db.session.add(secretaria)
        db.session.commit()
        
        # Registrar auditoria
        Auditoria.registrar(
            usuario_id=current_user.id,
            acao='CREATE',
            tabela='secretarias',
            registro_id=secretaria.id,
            dados_depois=secretaria.to_dict(),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.commit()
        
        flash(f'Secretaria {sigla} criada com sucesso!', 'success')
        return redirect(url_for('secretarias.lista'))
    
    return render_template('cadastros/secretarias_form.html')


@secretarias_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    """
    Editar secretaria existente
    """
    secretaria = Secretaria.query.get_or_404(id)
    
    if request.method == 'POST':
        # Guardar dados anteriores para auditoria
        dados_antes = secretaria.to_dict()
        
        nome = request.form.get('nome', '').strip()
        sigla = request.form.get('sigla', '').strip().upper()
        ativa = request.form.get('ativa', 'on') == 'on'
        
        # Validações
        if not nome:
            flash('Nome é obrigatório', 'danger')
            return render_template('cadastros/secretarias_form.html', secretaria=secretaria)
        
        valido, msg = Validacoes.validar_sigla_secretaria(sigla)
        if not valido:
            flash(msg, 'danger')
            return render_template('cadastros/secretarias_form.html', secretaria=secretaria)
        
        # Verificar se sigla já existe (exceto a atual)
        existe = Secretaria.buscar_por_sigla(sigla)
        if existe and existe.id != secretaria.id:
            flash(f'Já existe outra secretaria com a sigla {sigla}', 'danger')
            return render_template('cadastros/secretarias_form.html', secretaria=secretaria)
        
        # Atualizar
        secretaria.nome = nome
        secretaria.sigla = sigla
        secretaria.ativa = ativa
        
        db.session.commit()
        
        # Registrar auditoria
        Auditoria.registrar(
            usuario_id=current_user.id,
            acao='UPDATE',
            tabela='secretarias',
            registro_id=secretaria.id,
            dados_antes=dados_antes,
            dados_depois=secretaria.to_dict(),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.commit()
        
        flash(f'Secretaria {sigla} atualizada com sucesso!', 'success')
        return redirect(url_for('secretarias.lista'))
    
    return render_template('cadastros/secretarias_form.html', secretaria=secretaria)


@secretarias_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir(id):
    """
    Excluir secretaria
    """
    secretaria = Secretaria.query.get_or_404(id)
    
    # Verificar se tem servidores vinculados
    if secretaria.servidores.count() > 0:
        flash(f'Não é possível excluir a secretaria {secretaria.sigla} pois há servidores vinculados', 'danger')
        return redirect(url_for('secretarias.lista'))
    
    # Guardar dados para auditoria
    dados_antes = secretaria.to_dict()
    sigla = secretaria.sigla
    
    db.session.delete(secretaria)
    db.session.commit()
    
    # Registrar auditoria
    Auditoria.registrar(
        usuario_id=current_user.id,
        acao='DELETE',
        tabela='secretarias',
        registro_id=id,
        dados_antes=dados_antes,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    db.session.commit()
    
    flash(f'Secretaria {sigla} excluída com sucesso!', 'success')
    return redirect(url_for('secretarias.lista'))


@secretarias_bp.route('/toggle-ativa/<int:id>', methods=['POST'])
@login_required
def toggle_ativa(id):
    """
    Ativar/Desativar secretaria
    """
    secretaria = Secretaria.query.get_or_404(id)
    
    # Guardar dados anteriores
    dados_antes = secretaria.to_dict()
    
    # Alternar status
    secretaria.ativa = not secretaria.ativa
    
    db.session.commit()
    
    # Registrar auditoria
    Auditoria.registrar(
        usuario_id=current_user.id,
        acao='UPDATE',
        tabela='secretarias',
        registro_id=secretaria.id,
        dados_antes=dados_antes,
        dados_depois=secretaria.to_dict(),
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    db.session.commit()
    
    status = 'ativada' if secretaria.ativa else 'desativada'
    flash(f'Secretaria {secretaria.sigla} {status} com sucesso!', 'success')
    
    return redirect(url_for('secretarias.lista'))


@secretarias_bp.route('/api/listar-ativas')
@login_required
def api_listar_ativas():
    """
    API para listar secretarias ativas (para selects)
    """
    secretarias = Secretaria.listar_ativas().all()
    
    return jsonify([
        {
            'id': s.id,
            'nome': s.nome,
            'sigla': s.sigla
        }
        for s in secretarias
    ])