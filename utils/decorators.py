"""
Decorators customizados
"""

from functools import wraps
from flask import redirect, url_for, flash, request, abort
from flask_login import current_user


def login_required(f):
    """
    Decorator para rotas que requerem login
    Redireciona para login se usuário não estiver autenticado
    
    Usage:
        @app.route('/dashboard')
        @login_required
        def dashboard():
            return render_template('dashboard.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Você precisa estar logado para acessar esta página.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        # Verificar se usuário está ativo
        if not current_user.is_active:
            flash('Sua conta está inativa. Entre em contato com o administrador.', 'danger')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    
    return decorated_function


def admin_required(f):
    """
    Decorator para rotas que requerem privilégios de administrador
    Requer que o usuário esteja logado E seja admin
    
    Usage:
        @app.route('/admin/usuarios')
        @login_required
        @admin_required
        def gerenciar_usuarios():
            return render_template('admin/usuarios.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Você precisa estar logado para acessar esta página.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        # Verificar se usuário é admin
        # Nota: Adicione campo 'is_admin' no modelo Usuario se necessário
        # Por enquanto, apenas usuários com username 'admin' são considerados admins
        if current_user.username != 'admin':
            flash('Você não tem permissão para acessar esta página.', 'danger')
            abort(403)
        
        return f(*args, **kwargs)
    
    return decorated_function


def role_required(*roles):
    """
    Decorator para rotas que requerem roles específicas
    
    Args:
        *roles: Lista de roles permitidas
        
    Usage:
        @app.route('/financeiro')
        @login_required
        @role_required('admin', 'financeiro')
        def financeiro():
            return render_template('financeiro.html')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Você precisa estar logado para acessar esta página.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            # Verificar se usuário tem alguma das roles permitidas
            # Nota: Implemente campo 'role' no modelo Usuario se necessário
            user_role = getattr(current_user, 'role', 'user')
            
            if user_role not in roles:
                flash('Você não tem permissão para acessar esta página.', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def csrf_exempt(f):
    """
    Decorator para desabilitar proteção CSRF em rotas específicas
    Use com cuidado! Apenas para APIs ou rotas que realmente não precisam de CSRF
    
    Usage:
        @app.route('/api/webhook', methods=['POST'])
        @csrf_exempt
        def webhook():
            return jsonify({'status': 'ok'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    
    # Marcar função como isenta de CSRF
    decorated_function._csrf_exempt = True
    return decorated_function


def requires_fresh_login(f):
    """
    Decorator que requer login recente (fresh login)
    Útil para operações sensíveis que requerem re-autenticação
    
    Usage:
        @app.route('/conta/excluir')
        @login_required
        @requires_fresh_login
        def excluir_conta():
            return render_template('excluir_conta.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Você precisa estar logado para acessar esta página.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        # Verificar se login é fresh (Flask-Login)
        from flask_login import login_fresh
        
        if not login_fresh():
            flash('Por segurança, você precisa fazer login novamente para realizar esta ação.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        return f(*args, **kwargs)
    
    return decorated_function


def audit_action(action_name, table_name=None):
    """
    Decorator para registrar ações na auditoria automaticamente
    
    Args:
        action_name: Nome da ação (CREATE, UPDATE, DELETE, etc.)
        table_name: Nome da tabela (opcional)
        
    Usage:
        @app.route('/servidores/novo', methods=['POST'])
        @login_required
        @audit_action('CREATE', 'servidores')
        def criar_servidor():
            # ... código ...
            return redirect(url_for('servidores.lista'))
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from models.auditoria import Auditoria
            from utils.database import db
            
            # Executar função
            result = f(*args, **kwargs)
            
            # Registrar auditoria
            try:
                user_id = current_user.id if current_user.is_authenticated else None
                ip_address = request.remote_addr
                user_agent = request.user_agent.string
                
                Auditoria.registrar(
                    usuario_id=user_id,
                    acao=action_name,
                    tabela=table_name,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                db.session.commit()
            except Exception as e:
                # Não falhar a requisição se auditoria falhar
                print(f'Erro ao registrar auditoria: {e}')
            
            return result
        
        return decorated_function
    
    return decorator


def limit_content_length(max_length):
    """
    Decorator para limitar tamanho de upload
    
    Args:
        max_length: Tamanho máximo em bytes
        
    Usage:
        @app.route('/upload', methods=['POST'])
        @login_required
        @limit_content_length(5 * 1024 * 1024)  # 5MB
        def upload_file():
            return 'Upload realizado'
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            content_length = request.content_length
            
            if content_length and content_length > max_length:
                flash(f'Arquivo muito grande. Tamanho máximo: {max_length / (1024*1024):.1f} MB', 'danger')
                abort(413)  # Request Entity Too Large
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def cache_response(timeout=300):
    """
    Decorator para cache de resposta (simples)
    
    Args:
        timeout: Tempo de cache em segundos (padrão: 5 minutos)
        
    Usage:
        @app.route('/api/estatisticas')
        @cache_response(timeout=600)
        def estatisticas():
            return jsonify(calcular_estatisticas())
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Cache simples baseado em tempo
            # Para cache mais robusto, use Flask-Caching
            
            result = f(*args, **kwargs)
            
            # Adicionar headers de cache
            if hasattr(result, 'headers'):
                result.headers['Cache-Control'] = f'public, max-age={timeout}'
            
            return result
        
        return decorated_function
    
    return decorator


def ajax_required(f):
    """
    Decorator que permite apenas requisições AJAX
    
    Usage:
        @app.route('/api/buscar-servidor')
        @login_required
        @ajax_required
        def buscar_servidor():
            return jsonify({'resultado': 'ok'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_xhr and not request.is_json:
            abort(400)  # Bad Request
        
        return f(*args, **kwargs)
    
    return decorated_function


def validate_json(*required_fields):
    """
    Decorator para validar campos obrigatórios em JSON
    
    Args:
        *required_fields: Lista de campos obrigatórios
        
    Usage:
        @app.route('/api/criar', methods=['POST'])
        @validate_json('nome', 'email')
        def criar():
            data = request.get_json()
            return jsonify({'status': 'ok'})
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return {'error': 'Content-Type deve ser application/json'}, 400
            
            data = request.get_json()
            
            # Verificar campos obrigatórios
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                return {
                    'error': 'Campos obrigatórios ausentes',
                    'missing_fields': missing_fields
                }, 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator