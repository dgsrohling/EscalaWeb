"""
Validações de negócio
"""

from datetime import date
import calendar


class Validacoes:
    """
    Classe para validações de regras de negócio
    """
    
    @staticmethod
    def validar_competencia(mes, ano):
        """
        Valida se mês e ano são válidos
        
        Args:
            mes: Número do mês (1-12)
            ano: Ano (YYYY)
            
        Returns:
            tuple: (bool, str) - (válido, mensagem_erro)
        """
        try:
            mes = int(mes)
            ano = int(ano)
        except (ValueError, TypeError):
            return False, 'Mês e ano devem ser números'
        
        if not (1 <= mes <= 12):
            return False, 'Mês deve estar entre 1 e 12'
        
        if not (2020 <= ano <= 2100):
            return False, 'Ano deve estar entre 2020 e 2100'
        
        return True, ''
    
    @staticmethod
    def validar_dia_mes(dia, mes, ano):
        """
        Valida se o dia é válido para o mês/ano especificado
        
        Args:
            dia: Dia do mês
            mes: Mês (1-12)
            ano: Ano (YYYY)
            
        Returns:
            tuple: (bool, str) - (válido, mensagem_erro)
        """
        # Validar competência primeiro
        valido_comp, msg_comp = Validacoes.validar_competencia(mes, ano)
        if not valido_comp:
            return False, msg_comp
        
        try:
            dia = int(dia)
        except (ValueError, TypeError):
            return False, 'Dia deve ser um número'
        
        # Obter número de dias no mês
        dias_no_mes = calendar.monthrange(ano, mes)[1]
        
        if not (1 <= dia <= dias_no_mes):
            return False, f'Dia deve estar entre 1 e {dias_no_mes} para este mês'
        
        return True, ''
    
    @staticmethod
    def validar_tipo_grupo(tipo_grupo):
        """
        Valida se o tipo de grupo é válido
        
        Args:
            tipo_grupo: Tipo de grupo
            
        Returns:
            tuple: (bool, str) - (válido, mensagem_erro)
        """
        tipos_validos = ['GERAL', 'SAUDE_17H', 'SAUDE_17H30']
        
        if tipo_grupo not in tipos_validos:
            return False, f'Tipo de grupo deve ser um de: {", ".join(tipos_validos)}'
        
        return True, ''
    
    @staticmethod
    def validar_tipo_escala(tipo_escala):
        """
        Valida se o tipo de escala é válido
        
        Args:
            tipo_escala: Tipo de escala
            
        Returns:
            tuple: (bool, str) - (válido, mensagem_erro)
        """
        tipos_validos = ['GERAL', 'SAUDE']
        
        if tipo_escala not in tipos_validos:
            return False, f'Tipo de escala deve ser um de: {", ".join(tipos_validos)}'
        
        return True, ''
    
    @staticmethod
    def validar_status_escala(status):
        """
        Valida se o status da escala é válido
        
        Args:
            status: Status da escala
            
        Returns:
            tuple: (bool, str) - (válido, mensagem_erro)
        """
        status_validos = ['RASCUNHO', 'PUBLICADA', 'FINALIZADA', 'CANCELADA']
        
        if status not in status_validos:
            return False, f'Status deve ser um de: {", ".join(status_validos)}'
        
        return True, ''
    
    @staticmethod
    def validar_conflito_escala(servidor_id, escala_id, dia_mes, db_session):
        """
        Valida se já existe distribuição para o servidor neste dia
        
        Args:
            servidor_id: ID do servidor
            escala_id: ID da escala
            dia_mes: Dia do mês
            db_session: Sessão do banco de dados
            
        Returns:
            tuple: (bool, str) - (válido, mensagem_erro)
        """
        from models.escala_distribuicao import EscalaDistribuicao
        
        conflito = EscalaDistribuicao.verificar_conflito(servidor_id, escala_id, dia_mes)
        
        if conflito:
            return False, f'Servidor já está escalado para o dia {dia_mes}'
        
        return True, ''
    
    @staticmethod
    def validar_matricula(matricula):
        """
        Valida formato de matrícula
        
        Args:
            matricula: Matrícula do servidor
            
        Returns:
            tuple: (bool, str) - (válido, mensagem_erro)
        """
        if not matricula:
            return False, 'Matrícula é obrigatória'
        
        matricula_str = str(matricula).strip()
        
        if len(matricula_str) < 3:
            return False, 'Matrícula deve ter pelo menos 3 caracteres'
        
        if len(matricula_str) > 20:
            return False, 'Matrícula não pode ter mais de 20 caracteres'
        
        return True, ''
    
    @staticmethod
    def validar_nome(nome):
        """
        Valida nome de servidor
        
        Args:
            nome: Nome completo
            
        Returns:
            tuple: (bool, str) - (válido, mensagem_erro)
        """
        if not nome:
            return False, 'Nome é obrigatório'
        
        nome = nome.strip()
        
        if len(nome) < 3:
            return False, 'Nome deve ter pelo menos 3 caracteres'
        
        if len(nome) > 200:
            return False, 'Nome não pode ter mais de 200 caracteres'
        
        # Verificar se tem pelo menos 2 palavras (nome e sobrenome)
        palavras = nome.split()
        if len(palavras) < 2:
            return False, 'Informe nome e sobrenome'
        
        return True, ''
    
    @staticmethod
    def validar_email(email):
        """
        Valida formato de email
        
        Args:
            email: Email
            
        Returns:
            tuple: (bool, str) - (válido, mensagem_erro)
        """
        if not email:
            return True, ''  # Email é opcional
        
        import re
        padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(padrao, email):
            return False, 'Email inválido'
        
        return True, ''
    
    @staticmethod
    def validar_sigla_secretaria(sigla):
        """
        Valida sigla de secretaria
        
        Args:
            sigla: Sigla
            
        Returns:
            tuple: (bool, str) - (válido, mensagem_erro)
        """
        if not sigla:
            return False, 'Sigla é obrigatória'
        
        sigla = sigla.strip()
        
        if len(sigla) < 2:
            return False, 'Sigla deve ter pelo menos 2 caracteres'
        
        if len(sigla) > 20:
            return False, 'Sigla não pode ter mais de 20 caracteres'
        
        # Verificar se contém apenas letras, números e alguns caracteres especiais
        import re
        if not re.match(r'^[A-Z0-9\-_]+$', sigla.upper()):
            return False, 'Sigla deve conter apenas letras, números, hífens e underscores'
        
        return True, ''
    
    @staticmethod
    def validar_transicao_status(status_atual, status_novo):
        """
        Valida se a transição de status é permitida
        
        Args:
            status_atual: Status atual da escala
            status_novo: Novo status desejado
            
        Returns:
            tuple: (bool, str) - (válido, mensagem_erro)
        """
        # Transições permitidas
        transicoes = {
            'RASCUNHO': ['PUBLICADA', 'CANCELADA'],
            'PUBLICADA': ['FINALIZADA', 'CANCELADA'],
            'FINALIZADA': [],  # Não pode mudar de finalizada
            'CANCELADA': []  # Não pode mudar de cancelada
        }
        
        if status_novo not in transicoes.get(status_atual, []):
            return False, f'Não é possível mudar de {status_atual} para {status_novo}'
        
        return True, ''
    
    @staticmethod
    def validar_pode_editar_escala(escala):
        """
        Valida se uma escala pode ser editada
        
        Args:
            escala: Objeto Escala
            
        Returns:
            tuple: (bool, str) - (válido, mensagem_erro)
        """
        if escala.status in ['FINALIZADA', 'CANCELADA']:
            return False, f'Não é possível editar escala {escala.status.lower()}'
        
        return True, ''
    
    @staticmethod
    def validar_pode_excluir_escala(escala):
        """
        Valida se uma escala pode ser excluída
        
        Args:
            escala: Objeto Escala
            
        Returns:
            tuple: (bool, str) - (válido, mensagem_erro)
        """
        if escala.status == 'FINALIZADA':
            return False, 'Não é possível excluir escala finalizada'
        
        return True, ''
    
    @staticmethod
    def validar_horario(hora_str):
        """
        Valida formato de horário HH:MM
        
        Args:
            hora_str: String de horário
            
        Returns:
            tuple: (bool, str) - (válido, mensagem_erro)
        """
        if not hora_str:
            return False, 'Horário é obrigatório'
        
        try:
            parts = hora_str.split(':')
            if len(parts) != 2:
                return False, 'Horário deve estar no formato HH:MM'
            
            hora, minuto = map(int, parts)
            
            if not (0 <= hora <= 23):
                return False, 'Hora deve estar entre 00 e 23'
            
            if not (0 <= minuto <= 59):
                return False, 'Minuto deve estar entre 00 e 59'
            
            return True, ''
        except:
            return False, 'Horário inválido'
    
    @staticmethod
    def validar_lista_dias(dias, mes, ano):
        """
        Valida uma lista de dias para um mês/ano
        
        Args:
            dias: Lista de dias
            mes: Mês
            ano: Ano
            
        Returns:
            tuple: (bool, str) - (válido, mensagem_erro)
        """
        if not dias:
            return False, 'Nenhum dia informado'
        
        if not isinstance(dias, (list, tuple)):
            return False, 'Dias devem ser uma lista'
        
        dias_no_mes = calendar.monthrange(ano, mes)[1]
        
        for dia in dias:
            try:
                dia_int = int(dia)
                if not (1 <= dia_int <= dias_no_mes):
                    return False, f'Dia {dia_int} inválido para este mês'
            except (ValueError, TypeError):
                return False, f'Dia inválido: {dia}'
        
        return True, ''