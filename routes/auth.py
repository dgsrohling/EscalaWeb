"""
Rotas de autenticação (login/logout)
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from models.usuario import Usuario
from models.auditoria import Auditoria
from utils.database import db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Página de login
    """
    # Se já está logado, redirecionar para dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        # Validar campos
        if not username or not password:
            flash('Usuário e senha são obrigatórios', 'danger')
            return render_template('auth/login.html')
        
        # Buscar usuário
        usuario = Usuario.buscar_por_username(username)
        
        # Verificar credenciais
        if not usuario or not usuario.check_password(password):
            flash('Usuário ou senha incorretos', 'danger')
            
            # Registrar tentativa de login falha
            Auditoria.registrar(
                usuario_id=None,
                acao='LOGIN_FAILED',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            db.session.commit()
            
            return render_template('auth/login.html')
        
        # Verificar se usuário está ativo
        if not usuario.ativo:
            flash('Sua conta está inativa. Entre em contato com o administrador.', 'danger')
            return render_template('auth/login.html')
        
        # Fazer login
        login_user(usuario, remember=remember)
        
        # Registrar login na auditoria
        Auditoria.registrar(
            usuario_id=usuario.id,
            acao='LOGIN',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.commit()
        
        flash(f'Bem-vindo, {usuario.nome_completo}!', 'success')
        
        # Redirecionar para página solicitada ou dashboard
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        
        return redirect(url_for('dashboard.index'))
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    """
    Logout do usuário
    """
    if current_user.is_authenticated:
        # Registrar logout na auditoria
        Auditoria.registrar(
            usuario_id=current_user.id,
            acao='LOGOUT',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.commit()
        
        logout_user()
        flash('Logout realizado com sucesso', 'info')
    
    return redirect(url_for('auth.login'))


@auth_bp.route('/')
def index():
    """
    Rota raiz - redireciona para login ou dashboard
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    return redirect(url_for('auth.login'))