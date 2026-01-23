"""
Calculador de horas extras e adicional noturno
"""

from datetime import datetime, time, timedelta


class CalculadorHoras:
    """
    Classe para cálculo de horas extras e adicional noturno
    """
    
    # Horários padrão de sobreaviso
    HORARIOS_SOBREAVISO = {
        'GERAL': {'inicio': time(17, 0), 'fim': time(8, 0)},
        'SAUDE_17H': {'inicio': time(17, 0), 'fim': time(8, 0)},
        'SAUDE_17H30': {'inicio': time(17, 30), 'fim': time(8, 0)}
    }
    
    # Horário de adicional noturno (legislação trabalhista)
    HORARIO_NOTURNO_INICIO = time(22, 0)
    HORARIO_NOTURNO_FIM = time(5, 0)
    
    @staticmethod
    def calcular_horas_trabalhadas(hora_inicio, hora_fim):
        """
        Calcula o total de horas trabalhadas entre dois horários
        
        Args:
            hora_inicio: time object ou string HH:MM
            hora_fim: time object ou string HH:MM
            
        Returns:
            int: Total de minutos trabalhados
        """
        # Converter strings para time se necessário
        if isinstance(hora_inicio, str):
            h, m = map(int, hora_inicio.split(':'))
            hora_inicio = time(h, m)
        
        if isinstance(hora_fim, str):
            h, m = map(int, hora_fim.split(':'))
            hora_fim = time(h, m)
        
        # Converter time para datetime para facilitar cálculo
        hoje = datetime.today()
        dt_inicio = datetime.combine(hoje, hora_inicio)
        dt_fim = datetime.combine(hoje, hora_fim)
        
        # Se fim < início, significa que passou da meia-noite
        if dt_fim < dt_inicio:
            dt_fim += timedelta(days=1)
        
        diferenca = dt_fim - dt_inicio
        return int(diferenca.total_seconds() / 60)
    
    @staticmethod
    def calcular_adicional_noturno(hora_inicio, hora_fim):
        """
        Calcula o adicional noturno (22h às 05h)
        
        Args:
            hora_inicio: time object ou string HH:MM
            hora_fim: time object ou string HH:MM
            
        Returns:
            int: Total de minutos de adicional noturno
        """
        # Converter strings para time se necessário
        if isinstance(hora_inicio, str):
            h, m = map(int, hora_inicio.split(':'))
            hora_inicio = time(h, m)
        
        if isinstance(hora_fim, str):
            h, m = map(int, hora_fim.split(':'))
            hora_fim = time(h, m)
        
        hoje = datetime.today()
        amanha = hoje + timedelta(days=1)
        
        # Converter para datetime
        dt_inicio = datetime.combine(hoje, hora_inicio)
        dt_fim = datetime.combine(hoje, hora_fim)
        
        # Se fim < início, passou da meia-noite
        if dt_fim < dt_inicio:
            dt_fim = datetime.combine(amanha, hora_fim)
        
        # Período noturno: 22:00 às 05:00
        dt_noturno_inicio = datetime.combine(hoje, CalculadorHoras.HORARIO_NOTURNO_INICIO)
        dt_noturno_fim = datetime.combine(amanha, CalculadorHoras.HORARIO_NOTURNO_FIM)
        
        # Calcular interseção entre período trabalhado e período noturno
        inicio_overlap = max(dt_inicio, dt_noturno_inicio)
        fim_overlap = min(dt_fim, dt_noturno_fim)
        
        if fim_overlap > inicio_overlap:
            diferenca = fim_overlap - inicio_overlap
            return int(diferenca.total_seconds() / 60)
        
        return 0
    
    @staticmethod
    def calcular_plantao_completo(tipo_grupo, dia_mes, mes, ano):
        """
        Calcula um plantão completo com horários padrão do grupo
        
        Args:
            tipo_grupo: GERAL, SAUDE_17H ou SAUDE_17H30
            dia_mes: Dia do mês
            mes: Mês
            ano: Ano
            
        Returns:
            dict: {
                'hora_inicio': time,
                'hora_fim': time,
                'horas_trabalhadas': int (minutos),
                'adicional_noturno': int (minutos)
            }
        """
        horarios = CalculadorHoras.HORARIOS_SOBREAVISO.get(tipo_grupo)
        
        if not horarios:
            raise ValueError(f'Tipo de grupo inválido: {tipo_grupo}')
        
        hora_inicio = horarios['inicio']
        hora_fim = horarios['fim']
        
        horas_trabalhadas = CalculadorHoras.calcular_horas_trabalhadas(hora_inicio, hora_fim)
        adicional_noturno = CalculadorHoras.calcular_adicional_noturno(hora_inicio, hora_fim)
        
        return {
            'hora_inicio': hora_inicio,
            'hora_fim': hora_fim,
            'horas_trabalhadas': horas_trabalhadas,
            'adicional_noturno': adicional_noturno
        }
    
    @staticmethod
    def converter_minutos_para_horas(minutos):
        """
        Converte minutos para formato HH:MM
        
        Args:
            minutos: Total de minutos
            
        Returns:
            str: Formato HH:MM
        """
        if not minutos:
            return '00:00'
        
        horas = int(minutos // 60)
        mins = int(minutos % 60)
        return f'{horas:02d}:{mins:02d}'
    
    @staticmethod
    def converter_horas_para_minutos(hora_str):
        """
        Converte string HH:MM para minutos
        
        Args:
            hora_str: String no formato HH:MM
            
        Returns:
            int: Total de minutos
        """
        if not hora_str or ':' not in hora_str:
            return 0
        
        try:
            horas, minutos = map(int, hora_str.split(':'))
            return horas * 60 + minutos
        except:
            return 0
    
    @staticmethod
    def obter_horarios_grupo(tipo_grupo):
        """
        Retorna os horários de sobreaviso de um grupo
        
        Args:
            tipo_grupo: GERAL, SAUDE_17H ou SAUDE_17H30
            
        Returns:
            dict: {'inicio': time, 'fim': time}
        """
        return CalculadorHoras.HORARIOS_SOBREAVISO.get(tipo_grupo, {
            'inicio': time(17, 0),
            'fim': time(8, 0)
        })
    
    @staticmethod
    def formatar_horario(hora):
        """
        Formata time object para string HH:MM
        
        Args:
            hora: time object
            
        Returns:
            str: Horário formatado
        """
        if not hora:
            return ''
        
        if isinstance(hora, str):
            return hora
        
        return hora.strftime('%H:%M')
    
    @staticmethod
    def validar_horario(hora_str):
        """
        Valida se uma string é um horário válido
        
        Args:
            hora_str: String no formato HH:MM
            
        Returns:
            bool: True se válido
        """
        if not hora_str:
            return False
        
        try:
            parts = hora_str.split(':')
            if len(parts) != 2:
                return False
            
            hora, minuto = map(int, parts)
            
            if not (0 <= hora <= 23 and 0 <= minuto <= 59):
                return False
            
            return True
        except:
            return False