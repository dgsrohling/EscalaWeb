"""
Gerenciamento de banco de dados
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Instância global do SQLAlchemy
db = SQLAlchemy()
migrate = Migrate()


def init_db(app):
    """
    Inicializa o banco de dados com a aplicação Flask
    
    Args:
        app: Instância da aplicação Flask
    """
    db.init_app(app)
    migrate.init_app(app, db)
    
    with app.app_context():
        # Importar todos os modelos para que o SQLAlchemy os reconheça
        from models import usuario, secretaria, servidor, escala, escala_distribuicao, plantao_realizado, auditoria
        
        # Criar todas as tabelas
        db.create_all()
        
        # Criar usuário admin padrão se não existir
        criar_usuario_admin(app)


def criar_usuario_admin(app):
    """
    Cria usuário administrador padrão se não existir
    
    Args:
        app: Instância da aplicação Flask
    """
    from models.usuario import Usuario
    from flask_bcrypt import Bcrypt
    
    bcrypt = Bcrypt(app)
    
    # Verificar se já existe algum usuário
    usuario_existe = Usuario.query.first()
    
    if not usuario_existe:
        # Criar usuário admin padrão
        admin = Usuario(
            username=app.config['ADMIN_USERNAME'],
            nome_completo='Administrador do Sistema',
            email=app.config['ADMIN_EMAIL'],
            ativo=True
        )
        admin.set_password(app.config['ADMIN_PASSWORD'])
        
        db.session.add(admin)
        db.session.commit()
        
        app.logger.info(f'Usuário administrador criado: {admin.username}')
        print(f'✅ Usuário administrador criado: {admin.username}')
        print(f'   Senha padrão: {app.config["ADMIN_PASSWORD"]}')
        print('   ⚠️  ALTERE A SENHA APÓS O PRIMEIRO LOGIN!')


def reset_database(app):
    """
    CUIDADO: Remove todas as tabelas e recria o banco de dados
    Use apenas em desenvolvimento!
    
    Args:
        app: Instância da aplicação Flask
    """
    with app.app_context():
        db.drop_all()
        db.create_all()
        criar_usuario_admin(app)
        app.logger.warning('Banco de dados resetado!')
        print('⚠️  Banco de dados resetado!')