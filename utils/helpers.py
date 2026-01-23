"""
Funções auxiliares
"""

from datetime import datetime, date, time, timedelta
import calendar
import re
import unicodedata
from pathlib import Path


def formatar_data(data, formato='%d/%m/%Y'):
    """
    Formata uma data para string
    
    Args:
        data: objeto date ou datetime
        formato: formato desejado (padrão: dd/mm/yyyy)
        
    Returns:
        str: Data formatada ou string vazia se data for None
    """
    if not data:
        return ''
    
    if isinstance(data, str):
        return data
    
    return data.strftime(formato)


def formatar_data_hora(data_hora, formato='%d/%m/%Y %H:%M'):
    """
    Formata uma data/hora para string
    
    Args:
        data_hora: objeto datetime
        formato: formato desejado (padrão: dd/mm/yyyy hh:mm)
        
    Returns:
        str: Data/hora formatada ou string vazia se data_hora for None
    """
    if not data_hora:
        return ''
    
    if isinstance(data_hora, str):
        return data_hora
    
    return data_hora.strftime(formato)


def formatar_mes_ano(mes, ano):
    """
    Formata mês e ano para string legível
    
    Args:
        mes: Número do mês (1-12)
        ano: Ano (YYYY)
        
    Returns:
        str: Formato "Janeiro/2025"
    """
    meses = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]
    
    if not (1 <= mes <= 12):
        return f'{mes}/{ano}'
    
    return f'{meses[mes - 1]}/{ano}'


def mes_em_portugues(mes):
    """
    Retorna o nome do mês em português
    
    Args:
        mes: Número do mês (1-12)
        
    Returns:
        str: Nome do mês
    """
    meses = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]
    
    if not (1 <= mes <= 12):
        return str(mes)
    
    return meses[mes - 1]


def dias_da_semana():
    """
    Retorna lista com os dias da semana em português
    
    Returns:
        list: ['Domingo', 'Segunda', 'Terça', ...]
    """
    return ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']


def obter_primeiro_dia_semana(mes, ano):
    """
    Retorna o dia da semana do primeiro dia do mês
    
    Args:
        mes: Número do mês (1-12)
        ano: Ano (YYYY)
        
    Returns:
        int: 0=Domingo, 1=Segunda, ..., 6=Sábado
    """
    primeiro_dia = date(ano, mes, 1)
    # weekday() retorna 0=Segunda, 6=Domingo
    # Convertemos para 0=Domingo, 6=Sábado
    dia_semana = primeiro_dia.weekday()
    return (dia_semana + 1) % 7


def obter_dias_mes(mes, ano):
    """
    Retorna o número de dias em um mês
    
    Args:
        mes: Número do mês (1-12)
        ano: Ano (YYYY)
        
    Returns:
        int: Número de dias (28-31)
    """
    return calendar.monthrange(ano, mes)[1]


def formatar_telefone(telefone):
    """
    Formata um telefone para o padrão brasileiro
    
    Args:
        telefone: String com números do telefone
        
    Returns:
        str: Telefone formatado ou original se inválido
    """
    if not telefone:
        return ''
    
    # Remove tudo que não é número
    numeros = re.sub(r'\D', '', telefone)
    
    # Formata conforme quantidade de dígitos
    if len(numeros) == 11:  # Celular com DDD
        return f'({numeros[:2]}) {numeros[2:7]}-{numeros[7:]}'
    elif len(numeros) == 10:  # Fixo com DDD
        return f'({numeros[:2]}) {numeros[2:6]}-{numeros[6:]}'
    elif len(numeros) == 9:  # Celular sem DDD
        return f'{numeros[:5]}-{numeros[5:]}'
    elif len(numeros) == 8:  # Fixo sem DDD
        return f'{numeros[:4]}-{numeros[4:]}'
    
    return telefone


def validar_email(email):
    """
    Valida formato de email
    
    Args:
        email: String com email
        
    Returns:
        bool: True se email é válido
    """
    if not email:
        return False
    
    padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(padrao, email) is not None


def validar_cpf(cpf):
    """
    Valida CPF brasileiro
    
    Args:
        cpf: String com CPF
        
    Returns:
        bool: True se CPF é válido
    """
    if not cpf:
        return False
    
    # Remove tudo que não é número
    cpf = re.sub(r'\D', '', cpf)
    
    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return False
    
    # Verifica se todos os dígitos são iguais
    if cpf == cpf[0] * 11:
        return False
    
    # Validação dos dígitos verificadores
    def calcular_digito(cpf_parcial):
        soma = 0
        for i, digito in enumerate(cpf_parcial):
            soma += int(digito) * (len(cpf_parcial) + 1 - i)
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto
    
    # Valida primeiro dígito
    if int(cpf[9]) != calcular_digito(cpf[:9]):
        return False
    
    # Valida segundo dígito
    if int(cpf[10]) != calcular_digito(cpf[:10]):
        return False
    
    return True


def gerar_nome_arquivo(nome_base, extensao, incluir_timestamp=True):
    """
    Gera nome de arquivo seguro
    
    Args:
        nome_base: Nome base do arquivo
        extensao: Extensão (.xlsx, .pdf, etc)
        incluir_timestamp: Se deve incluir timestamp no nome
        
    Returns:
        str: Nome do arquivo gerado
    """
    # Remove acentos e caracteres especiais
    nome_limpo = remover_acentos(nome_base)
    nome_limpo = re.sub(r'[^\w\s-]', '', nome_limpo)
    nome_limpo = re.sub(r'[-\s]+', '_', nome_limpo)
    nome_limpo = nome_limpo.strip('_')
    
    # Adiciona timestamp se solicitado
    if incluir_timestamp:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_final = f'{nome_limpo}_{timestamp}'
    else:
        nome_final = nome_limpo
    
    # Adiciona extensão
    if not extensao.startswith('.'):
        extensao = f'.{extensao}'
    
    return f'{nome_final}{extensao}'


def remover_acentos(texto):
    """
    Remove acentos de uma string
    
    Args:
        texto: String com acentos
        
    Returns:
        str: String sem acentos
    """
    if not texto:
        return ''
    
    # Normaliza e remove acentos
    nfkd = unicodedata.normalize('NFKD', texto)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)])


def converter_minutos_para_horas(minutos):
    """
    Converte minutos para formato HH:MM
    
    Args:
        minutos: Número de minutos
        
    Returns:
        str: Formato HH:MM
    """
    if not minutos:
        return '00:00'
    
    horas = int(minutos // 60)
    mins = int(minutos % 60)
    return f'{horas:02d}:{mins:02d}'


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


def calcular_diferenca_horas(hora_inicio, hora_fim):
    """
    Calcula diferença entre dois horários
    
    Args:
        hora_inicio: time object ou string HH:MM
        hora_fim: time object ou string HH:MM
        
    Returns:
        int: Diferença em minutos
    """
    # Converter strings para time se necessário
    if isinstance(hora_inicio, str):
        h, m = map(int, hora_inicio.split(':'))
        hora_inicio = time(h, m)
    
    if isinstance(hora_fim, str):
        h, m = map(int, hora_fim.split(':'))
        hora_fim = time(h, m)
    
    # Converter para datetime para calcular diferença
    hoje = date.today()
    dt_inicio = datetime.combine(hoje, hora_inicio)
    dt_fim = datetime.combine(hoje, hora_fim)
    
    # Se fim < início, passou da meia-noite
    if dt_fim < dt_inicio:
        dt_fim += timedelta(days=1)
    
    diferenca = dt_fim - dt_inicio
    return int(diferenca.total_seconds() / 60)


def calcular_adicional_noturno(hora_inicio, hora_fim, inicio_noturno='22:00', fim_noturno='05:00'):
    """
    Calcula adicional noturno entre dois horários
    
    Args:
        hora_inicio: time object ou string HH:MM
        hora_fim: time object ou string HH:MM
        inicio_noturno: Horário de início do período noturno (padrão 22:00)
        fim_noturno: Horário de fim do período noturno (padrão 05:00)
        
    Returns:
        int: Minutos de adicional noturno
    """
    # Converter strings para time se necessário
    if isinstance(hora_inicio, str):
        h, m = map(int, hora_inicio.split(':'))
        hora_inicio = time(h, m)
    
    if isinstance(hora_fim, str):
        h, m = map(int, hora_fim.split(':'))
        hora_fim = time(h, m)
    
    # Converter horários de período noturno
    h, m = map(int, inicio_noturno.split(':'))
    noturno_inicio = time(h, m)
    
    h, m = map(int, fim_noturno.split(':'))
    noturno_fim = time(h, m)
    
    # Converter para datetime
    hoje = date.today()
    amanha = hoje + timedelta(days=1)
    
    dt_inicio = datetime.combine(hoje, hora_inicio)
    dt_fim = datetime.combine(hoje, hora_fim)
    
    # Se fim < início, passou da meia-noite
    if dt_fim < dt_inicio:
        dt_fim = datetime.combine(amanha, hora_fim)
    
    # Período noturno
    dt_noturno_inicio = datetime.combine(hoje, noturno_inicio)
    dt_noturno_fim = datetime.combine(amanha, noturno_fim)
    
    # Calcular interseção
    inicio_overlap = max(dt_inicio, dt_noturno_inicio)
    fim_overlap = min(dt_fim, dt_noturno_fim)
    
    if fim_overlap > inicio_overlap:
        diferenca = fim_overlap - inicio_overlap
        return int(diferenca.total_seconds() / 60)
    
    return 0


def criar_diretorio_se_nao_existe(caminho):
    """
    Cria um diretório se ele não existir
    
    Args:
        caminho: Path ou string do caminho
        
    Returns:
        Path: Objeto Path do diretório
    """
    if isinstance(caminho, str):
        caminho = Path(caminho)
    
    caminho.mkdir(parents=True, exist_ok=True)
    return caminho


def arquivo_existe(caminho):
    """
    Verifica se um arquivo existe
    
    Args:
        caminho: Path ou string do caminho
        
    Returns:
        bool: True se o arquivo existe
    """
    if isinstance(caminho, str):
        caminho = Path(caminho)
    
    return caminho.exists() and caminho.is_file()


def obter_tamanho_arquivo(caminho):
    """
    Retorna o tamanho de um arquivo em formato legível
    
    Args:
        caminho: Path ou string do caminho
        
    Returns:
        str: Tamanho formatado (ex: "2.5 MB")
    """
    if isinstance(caminho, str):
        caminho = Path(caminho)
    
    if not caminho.exists():
        return '0 B'
    
    tamanho = caminho.stat().st_size
    
    # Converter para unidade apropriada
    for unidade in ['B', 'KB', 'MB', 'GB']:
        if tamanho < 1024.0:
            return f'{tamanho:.1f} {unidade}'
        tamanho /= 1024.0
    
    return f'{tamanho:.1f} TB'


def truncar_texto(texto, tamanho_max=50, sufixo='...'):
    """
    Trunca um texto se exceder o tamanho máximo
    
    Args:
        texto: Texto a truncar
        tamanho_max: Tamanho máximo
        sufixo: Sufixo a adicionar (padrão: ...)
        
    Returns:
        str: Texto truncado
    """
    if not texto:
        return ''
    
    if len(texto) <= tamanho_max:
        return texto
    
    return texto[:tamanho_max - len(sufixo)] + sufixo


def obter_iniciais(nome_completo):
    """
    Retorna as iniciais de um nome
    
    Args:
        nome_completo: Nome completo
        
    Returns:
        str: Iniciais (ex: "João Silva" -> "JS")
    """
    if not nome_completo:
        return ''
    
    palavras = nome_completo.strip().split()
    iniciais = ''.join([p[0].upper() for p in palavras if p])
    
    return iniciais[:3]  # Máximo 3 iniciais


def formatar_valor_monetario(valor, incluir_simbolo=True):
    """
    Formata valor monetário para o padrão brasileiro
    
    Args:
        valor: Valor numérico
        incluir_simbolo: Se deve incluir R$
        
    Returns:
        str: Valor formatado
    """
    if valor is None:
        valor = 0
    
    valor_formatado = f'{valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    
    if incluir_simbolo:
        return f'R$ {valor_formatado}'
    
    return valor_formatado