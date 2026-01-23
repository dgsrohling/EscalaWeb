"""
Rotas CRUD de servidores
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.servidor import Servidor
from models.secretaria import Secretaria
from models.auditoria import Auditoria
from services.validacoes import Validacoes
from utils.database import db

servidores_bp = Blueprint('servidores', __name__)


@servidores_bp.route('/')
@login_required
def lista():
    """
    Lista todos os servidores
    """
    # Filtros
    tipo_grupo = request.args.get('tipo_grupo', '')
    secretaria_id = request.args.get('secretaria_id', '', type=int)
    busca = request.args.get('busca', '').strip()
    
    # Query base
    query = Servidor.query
    
    # Aplicar filtros
    if tipo_grupo:
        query = query.filter_by(tipo_grupo=tipo_grupo)
    
    if secretaria_id:
        query = query.filter_by(secretaria_id=secretaria_id)
    
    if busca:
        query = query.filter(
            db.or_(
                Servidor.nome_completo.ilike(f'%{busca}%'),
                Servidor.matricula.ilike(f'%{busca}%')
            )
        )
    
    # Ordenar
    servidores = query.order_by(Servidor.nome_completo).all()
    
    # Buscar secretarias para filtro
    secretarias = Secretaria.listar_ativas().all()
    
    return render_template(
        'cadastros/servidores_lista.html',
        servidores=servidores,
        secretarias=secretarias,
        tipo_grupo=tipo_grupo,
        secretaria_id=secretaria_id,
        busca=busca
    )


@servidores_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    """
    Criar novo servidor
    """
    if request.method == 'POST':
        matricula = request.form.get('matricula', '').strip()
        nome_completo = request.form.get('nome_completo', '').strip()
        tipo_grupo = request.form.get('tipo_grupo', '')
        secretaria_id = request.form.get('secretaria_id', '', type=int) or None
        telefone = request.form.get('telefone', '').strip()
        email = request.form.get('email', '').strip()
        ativo = request.form.get('ativo', 'on') == 'on'
        
        # Validações
        valido, msg = Validacoes.validar_matricula(matricula)
        if not valido:
            flash(msg, 'danger')
            return render_template('cadastros/servidores_form.html',
                                 secretarias=Secretaria.listar_ativas().all())
        
        valido, msg = Validacoes.validar_nome(nome_completo)
        if not valido:
            flash(msg, 'danger')
            return render_template('cadastros/servidores_form.html',
                                 secretarias=Secretaria.listar_ativas().all())
        
        valido, msg = Validacoes.validar_tipo_grupo(tipo_grupo)
        if not valido:
            flash(msg, 'danger')
            return render_template('cadastros/servidores_form.html',
                                 secretarias=Secretaria.listar_ativas().all())
        
        if email:
            valido, msg = Validacoes.validar_email(email)
            if not valido:
                flash(msg, 'danger')
                return render_template('cadastros/servidores_form.html',
                                     secretarias=Secretaria.listar_ativas().all())
        
        # Verificar se matrícula já existe
        existe = Servidor.buscar_por_matricula(matricula)
        if existe:
            flash(f'Já existe um servidor com a matrícula {matricula}', 'danger')
            return render_template('cadastros/servidores_form.html',
                                 secretarias=Secretaria.listar_ativas().all())
        
        # Validar secretaria para tipo GERAL
        if tipo_grupo == 'GERAL' and not secretaria_id:
            flash('Secretaria é obrigatória para servidores do tipo GERAL', 'danger')
            return render_template('cadastros/servidores_form.html',
                                 secretarias=Secretaria.listar_ativas().all())
        
        # Criar servidor
        servidor = Servidor(
            matricula=matricula,
            nome_completo=nome_completo,
            tipo_grupo=tipo_grupo,
            secretaria_id=secretaria_id,
            telefone=telefone,
            email=email,
            ativo=ativo
        )
        
        db.session.add(servidor)
        db.session.commit()
        
        # Registrar auditoria
        Auditoria.registrar(
            usuario_id=current_user.id,
            acao='CREATE',
            tabela='servidores',
            registro_id=servidor.id,
            dados_depois=servidor.to_dict(),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.commit()
        
        flash(f'Servidor {matricula} - {nome_completo} criado com sucesso!', 'success')
        return redirect(url_for('servidores.lista'))
    
    # GET
    secretarias = Secretaria.listar_ativas().all()
    return render_template('cadastros/servidores_form.html', secretarias=secretarias)


@servidores_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    """
    Editar servidor existente
    """
    servidor = Servidor.query.get_or_404(id)
    
    if request.method == 'POST':
        # Guardar dados anteriores
        dados_antes = servidor.to_dict()
        
        matricula = request.form.get('matricula', '').strip()
        nome_completo = request.form.get('nome_completo', '').strip()
        tipo_grupo = request.form.get('tipo_grupo', '')
        secretaria_id = request.form.get('secretaria_id', '', type=int) or None
        telefone = request.form.get('telefone', '').strip()
        email = request.form.get('email', '').strip()
        ativo = request.form.get('ativo', 'on') == 'on'
        
        # Validações
        valido, msg = Validacoes.validar_matricula(matricula)
        if not valido:
            flash(msg, 'danger')
            return render_template('cadastros/servidores_form.html',
                                 servidor=servidor,
                                 secretarias=Secretaria.listar_ativas().all())
        
        valido, msg = Validacoes.validar_nome(nome_completo)
        if not valido:
            flash(msg, 'danger')
            return render_template('cadastros/servidores_form.html',
                                 servidor=servidor,
                                 secretarias=Secretaria.listar_ativas().all())
        
        valido, msg = Validacoes.validar_tipo_grupo(tipo_grupo)
        if not valido:
            flash(msg, 'danger')
            return render_template('cadastros/servidores_form.html',
                                 servidor=servidor,
                                 secretarias=Secretaria.listar_ativas().all())
        
        if email:
            valido, msg = Validacoes.validar_email(email)
            if not valido:
                flash(msg, 'danger')
                return render_template('cadastros/servidores_form.html',
                                     servidor=servidor,
                                     secretarias=Secretaria.listar_ativas().all())
        
        # Verificar matrícula única (exceto a atual)
        existe = Servidor.buscar_por_matricula(matricula)
        if existe and existe.id != servidor.id:
            flash(f'Já existe outro servidor com a matrícula {matricula}', 'danger')
            return render_template('cadastros/servidores_form.html',
                                 servidor=servidor,
                                 secretarias=Secretaria.listar_ativas().all())
        
        # Atualizar
        servidor.matricula = matricula
        servidor.nome_completo = nome_completo
        servidor.tipo_grupo = tipo_grupo
        servidor.secretaria_id = secretaria_id
        servidor.telefone = telefone
        servidor.email = email
        servidor.ativo = ativo
        
        db.session.commit()
        
        # Registrar auditoria
        Auditoria.registrar(
            usuario_id=current_user.id,
            acao='UPDATE',
            tabela='servidores',
            registro_id=servidor.id,
            dados_antes=dados_antes,
            dados_depois=servidor.to_dict(),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.commit()
        
        flash(f'Servidor {matricula} atualizado com sucesso!', 'success')
        return redirect(url_for('servidores.lista'))
    
    # GET
    secretarias = Secretaria.listar_ativas().all()
    return render_template('cadastros/servidores_form.html',
                         servidor=servidor,
                         secretarias=secretarias)


@servidores_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir(id):
    """
    Excluir servidor
    """
    servidor = Servidor.query.get_or_404(id)
    
    # Verificar se tem escalas ou plantões vinculados
    if servidor.distribuicoes.count() > 0:
        flash(f'Não é possível excluir o servidor {servidor.matricula} pois há escalas vinculadas', 'danger')
        return redirect(url_for('servidores.lista'))
    
    if servidor.plantoes_realizados.count() > 0:
        flash(f'Não é possível excluir o servidor {servidor.matricula} pois há plantões registrados', 'danger')
        return redirect(url_for('servidores.lista'))
    
    # Guardar dados
    dados_antes = servidor.to_dict()
    matricula = servidor.matricula
    
    db.session.delete(servidor)
    db.session.commit()
    
    # Registrar auditoria
    Auditoria.registrar(
        usuario_id=current_user.id,
        acao='DELETE',
        tabela='servidores',
        registro_id=id,
        dados_antes=dados_antes,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    db.session.commit()
    
    flash(f'Servidor {matricula} excluído com sucesso!', 'success')
    return redirect(url_for('servidores.lista'))


@servidores_bp.route('/toggle-ativo/<int:id>', methods=['POST'])
@login_required
def toggle_ativo(id):
    """
    Ativar/Desativar servidor
    """
    servidor = Servidor.query.get_or_404(id)
    
    dados_antes = servidor.to_dict()
    servidor.ativo = not servidor.ativo
    
    db.session.commit()
    
    Auditoria.registrar(
        usuario_id=current_user.id,
        acao='UPDATE',
        tabela='servidores',
        registro_id=servidor.id,
        dados_antes=dados_antes,
        dados_depois=servidor.to_dict(),
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    db.session.commit()
    
    status = 'ativado' if servidor.ativo else 'desativado'
    flash(f'Servidor {servidor.matricula} {status} com sucesso!', 'success')
    
    return redirect(url_for('servidores.lista'))


@servidores_bp.route('/api/listar-por-tipo/<tipo_grupo>')
@login_required
def api_listar_por_tipo(tipo_grupo):
    """
    API para listar servidores por tipo de grupo
    """
    servidores = Servidor.listar_por_tipo_grupo(tipo_grupo).all()
    
    return jsonify([
        {
            'id': s.id,
            'matricula': s.matricula,
            'nome_completo': s.nome_completo,
            'tipo_grupo': s.tipo_grupo
        }
        for s in servidores
    ])