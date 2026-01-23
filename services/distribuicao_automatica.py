"""
Lógica de distribuição automática de escalas
"""

import calendar
from models.escala_distribuicao import EscalaDistribuicao
from utils.database import db


class DistribuicaoAutomatica:
    """
    Classe para distribuição automática de servidores em escalas
    """
    
    @staticmethod
    def distribuir_rodizio_sequencial(escala_id, servidores_ids, mes, ano):
        """
        Distribui servidores em rodízio sequencial ao longo do mês
        
        Algoritmo:
        - Divide os dias do mês igualmente entre os servidores
        - Cada servidor fica escalado em sequência
        - Ex: 3 servidores, 30 dias → cada um fica ~10 dias seguidos
        
        Args:
            escala_id: ID da escala
            servidores_ids: Lista de IDs dos servidores
            mes: Mês (1-12)
            ano: Ano (YYYY)
            
        Returns:
            list: Lista de EscalaDistribuicao criadas
        """
        if not servidores_ids:
            return []
        
        # Número de dias no mês
        dias_no_mes = calendar.monthrange(ano, mes)[1]
        
        # Número de servidores
        num_servidores = len(servidores_ids)
        
        # Distribuir dias
        distribuicoes = []
        
        for dia in range(1, dias_no_mes + 1):
            # Determinar qual servidor fica neste dia (rodízio circular)
            indice_servidor = (dia - 1) % num_servidores
            servidor_id = servidores_ids[indice_servidor]
            
            # Criar distribuição
            dist = EscalaDistribuicao(
                escala_id=escala_id,
                servidor_id=servidor_id,
                dia_mes=dia
            )
            
            distribuicoes.append(dist)
            db.session.add(dist)
        
        return distribuicoes
    
    @staticmethod
    def distribuir_intercalado(escala_id, servidores_ids, mes, ano, dias_intervalo=1):
        """
        Distribui servidores de forma intercalada
        
        Algoritmo:
        - Cada servidor fica X dias, depois passa para o próximo
        - Padrão: 1 dia cada (alternando diariamente)
        
        Args:
            escala_id: ID da escala
            servidores_ids: Lista de IDs dos servidores
            mes: Mês (1-12)
            ano: Ano (YYYY)
            dias_intervalo: Quantos dias cada servidor fica antes de alternar
            
        Returns:
            list: Lista de EscalaDistribuicao criadas
        """
        if not servidores_ids:
            return []
        
        dias_no_mes = calendar.monthrange(ano, mes)[1]
        num_servidores = len(servidores_ids)
        
        distribuicoes = []
        indice_servidor_atual = 0
        contador_dias = 0
        
        for dia in range(1, dias_no_mes + 1):
            # Servidor atual
            servidor_id = servidores_ids[indice_servidor_atual]
            
            # Criar distribuição
            dist = EscalaDistribuicao(
                escala_id=escala_id,
                servidor_id=servidor_id,
                dia_mes=dia
            )
            
            distribuicoes.append(dist)
            db.session.add(dist)
            
            # Incrementar contador
            contador_dias += 1
            
            # Trocar de servidor após X dias
            if contador_dias >= dias_intervalo:
                contador_dias = 0
                indice_servidor_atual = (indice_servidor_atual + 1) % num_servidores
        
        return distribuicoes
    
    @staticmethod
    def distribuir_balanceado(escala_id, servidores_ids, mes, ano):
        """
        Distribui servidores de forma balanceada
        
        Algoritmo:
        - Cada servidor recebe aproximadamente o mesmo número de dias
        - Dias são distribuídos ao longo do mês
        
        Args:
            escala_id: ID da escala
            servidores_ids: Lista de IDs dos servidores
            mes: Mês (1-12)
            ano: Ano (YYYY)
            
        Returns:
            list: Lista de EscalaDistribuicao criadas
        """
        if not servidores_ids:
            return []
        
        dias_no_mes = calendar.monthrange(ano, mes)[1]
        num_servidores = len(servidores_ids)
        
        # Calcular quantos dias cada servidor deve ter
        dias_por_servidor = dias_no_mes // num_servidores
        dias_extras = dias_no_mes % num_servidores
        
        distribuicoes = []
        dia_atual = 1
        
        for i, servidor_id in enumerate(servidores_ids):
            # Servidor recebe dias_por_servidor + 1 extra se necessário
            dias_deste_servidor = dias_por_servidor
            if i < dias_extras:
                dias_deste_servidor += 1
            
            # Criar distribuições para este servidor
            for _ in range(dias_deste_servidor):
                if dia_atual <= dias_no_mes:
                    dist = EscalaDistribuicao(
                        escala_id=escala_id,
                        servidor_id=servidor_id,
                        dia_mes=dia_atual
                    )
                    
                    distribuicoes.append(dist)
                    db.session.add(dist)
                    dia_atual += 1
        
        return distribuicoes
    
    @staticmethod
    def distribuir_fins_de_semana_alternados(escala_id, servidores_ids, mes, ano):
        """
        Distribui servidores priorizando alternância de fins de semana
        
        Algoritmo:
        - Servidores alternam entre finais de semana
        - Dias úteis são distribuídos sequencialmente
        
        Args:
            escala_id: ID da escala
            servidores_ids: Lista de IDs dos servidores
            mes: Mês (1-12)
            ano: Ano (YYYY)
            
        Returns:
            list: Lista de EscalaDistribuicao criadas
        """
        if not servidores_ids:
            return []
        
        dias_no_mes = calendar.monthrange(ano, mes)[1]
        num_servidores = len(servidores_ids)
        
        distribuicoes = []
        indice_servidor = 0
        indice_fim_semana = 0
        
        for dia in range(1, dias_no_mes + 1):
            # Verificar dia da semana (0=segunda, 6=domingo)
            from datetime import date
            data = date(ano, mes, dia)
            dia_semana = data.weekday()
            
            # Sábado (5) ou Domingo (6)
            if dia_semana in [5, 6]:
                # Alternar servidor a cada fim de semana
                servidor_id = servidores_ids[indice_fim_semana % num_servidores]
                if dia_semana == 6:  # Domingo - incrementa para próximo fim de semana
                    indice_fim_semana += 1
            else:
                # Dias úteis - rodízio normal
                servidor_id = servidores_ids[indice_servidor % num_servidores]
                indice_servidor += 1
            
            # Criar distribuição
            dist = EscalaDistribuicao(
                escala_id=escala_id,
                servidor_id=servidor_id,
                dia_mes=dia
            )
            
            distribuicoes.append(dist)
            db.session.add(dist)
        
        return distribuicoes
    
    @staticmethod
    def limpar_distribuicao_existente(escala_id):
        """
        Remove todas as distribuições existentes de uma escala
        
        Args:
            escala_id: ID da escala
            
        Returns:
            int: Número de distribuições removidas
        """
        distribuicoes = EscalaDistribuicao.query.filter_by(escala_id=escala_id).all()
        count = len(distribuicoes)
        
        for dist in distribuicoes:
            db.session.delete(dist)
        
        return count
    
    @staticmethod
    def redistribuir(escala_id, servidores_ids, mes, ano, modo='rodizio'):
        """
        Limpa distribuição existente e cria uma nova
        
        Args:
            escala_id: ID da escala
            servidores_ids: Lista de IDs dos servidores
            mes: Mês (1-12)
            ano: Ano (YYYY)
            modo: Modo de distribuição ('rodizio', 'intercalado', 'balanceado', 'fins_semana')
            
        Returns:
            list: Lista de EscalaDistribuicao criadas
        """
        # Limpar distribuição existente
        DistribuicaoAutomatica.limpar_distribuicao_existente(escala_id)
        
        # Criar nova distribuição conforme modo
        if modo == 'rodizio':
            return DistribuicaoAutomatica.distribuir_rodizio_sequencial(
                escala_id, servidores_ids, mes, ano
            )
        elif modo == 'intercalado':
            return DistribuicaoAutomatica.distribuir_intercalado(
                escala_id, servidores_ids, mes, ano
            )
        elif modo == 'balanceado':
            return DistribuicaoAutomatica.distribuir_balanceado(
                escala_id, servidores_ids, mes, ano
            )
        elif modo == 'fins_semana':
            return DistribuicaoAutomatica.distribuir_fins_de_semana_alternados(
                escala_id, servidores_ids, mes, ano
            )
        else:
            raise ValueError(f'Modo de distribuição inválido: {modo}')
    
    @staticmethod
    def obter_estatisticas_distribuicao(escala_id):
        """
        Retorna estatísticas sobre a distribuição de uma escala
        
        Args:
            escala_id: ID da escala
            
        Returns:
            dict: Estatísticas da distribuição
        """
        distribuicoes = EscalaDistribuicao.query.filter_by(escala_id=escala_id).all()
        
        if not distribuicoes:
            return {
                'total_dias': 0,
                'total_servidores': 0,
                'dias_por_servidor': {}
            }
        
        # Contar dias por servidor
        dias_por_servidor = {}
        for dist in distribuicoes:
            servidor_id = dist.servidor_id
            if servidor_id not in dias_por_servidor:
                dias_por_servidor[servidor_id] = {
                    'servidor_nome': dist.servidor.nome_completo if dist.servidor else 'Desconhecido',
                    'total_dias': 0,
                    'dias': []
                }
            
            dias_por_servidor[servidor_id]['total_dias'] += 1
            dias_por_servidor[servidor_id]['dias'].append(dist.dia_mes)
        
        return {
            'total_dias': len(distribuicoes),
            'total_servidores': len(dias_por_servidor),
            'dias_por_servidor': dias_por_servidor
        }