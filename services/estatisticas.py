"""
Cálculos de estatísticas e dashboard
"""

from sqlalchemy import func, desc
from models.servidor import Servidor
from models.plantao_realizado import PlantaoRealizado
from models.escala import Escala
from models.escala_distribuicao import EscalaDistribuicao
from utils.database import db
import calendar


class Estatisticas:
    """
    Classe para cálculos de estatísticas do sistema
    """
    
    @staticmethod
    def top_plantonistas(mes=None, ano=None, limite=10):
        """
        Retorna os servidores com mais horas trabalhadas
        
        Args:
            mes: Mês (opcional, None = todos)
            ano: Ano (opcional, None = todos)
            limite: Número de servidores a retornar
            
        Returns:
            list: Lista de dicts com servidor e total de horas
        """
        query = db.session.query(
            Servidor.id,
            Servidor.nome_completo,
            Servidor.matricula,
            func.sum(PlantaoRealizado.horas_trabalhadas).label('total_horas')
        ).join(
            PlantaoRealizado, Servidor.id == PlantaoRealizado.servidor_id
        )
        
        # Filtros opcionais
        if mes:
            query = query.filter(PlantaoRealizado.competencia_mes == mes)
        if ano:
            query = query.filter(PlantaoRealizado.competencia_ano == ano)
        
        # Agrupar e ordenar
        query = query.group_by(Servidor.id).order_by(desc('total_horas')).limit(limite)
        
        resultados = query.all()
        
        return [
            {
                'servidor_id': r.id,
                'nome': r.nome_completo,
                'matricula': r.matricula,
                'total_horas': r.total_horas or 0,
                'total_horas_display': PlantaoRealizado.get_horas_display(r.total_horas or 0)
            }
            for r in resultados
        ]
    
    @staticmethod
    def distribuicao_por_grupo(mes=None, ano=None):
        """
        Retorna a distribuição de plantões por grupo
        
        Args:
            mes: Mês (opcional)
            ano: Ano (opcional)
            
        Returns:
            dict: Distribuição por tipo de grupo
        """
        query = db.session.query(
            Servidor.tipo_grupo,
            func.count(PlantaoRealizado.id).label('total_plantoes'),
            func.sum(PlantaoRealizado.horas_trabalhadas).label('total_horas')
        ).join(
            PlantaoRealizado, Servidor.id == PlantaoRealizado.servidor_id
        )
        
        # Filtros opcionais
        if mes:
            query = query.filter(PlantaoRealizado.competencia_mes == mes)
        if ano:
            query = query.filter(PlantaoRealizado.competencia_ano == ano)
        
        # Agrupar
        query = query.group_by(Servidor.tipo_grupo)
        
        resultados = query.all()
        
        grupos = {}
        for r in resultados:
            grupos[r.tipo_grupo] = {
                'total_plantoes': r.total_plantoes,
                'total_horas': r.total_horas or 0,
                'total_horas_display': PlantaoRealizado.get_horas_display(r.total_horas or 0)
            }
        
        return grupos
    
    @staticmethod
    def estatisticas_gerais(mes=None, ano=None):
        """
        Retorna estatísticas gerais do sistema
        
        Args:
            mes: Mês (opcional)
            ano: Ano (opcional)
            
        Returns:
            dict: Estatísticas gerais
        """
        # Total de servidores ativos
        total_servidores = Servidor.query.filter_by(ativo=True).count()
        
        # Query base para plantões
        query_plantoes = PlantaoRealizado.query
        
        if mes:
            query_plantoes = query_plantoes.filter_by(competencia_mes=mes)
        if ano:
            query_plantoes = query_plantoes.filter_by(competencia_ano=ano)
        
        # Total de plantões
        total_plantoes = query_plantoes.count()
        
        # Total de horas
        total_horas = db.session.query(
            func.sum(PlantaoRealizado.horas_trabalhadas)
        )
        
        if mes:
            total_horas = total_horas.filter(PlantaoRealizado.competencia_mes == mes)
        if ano:
            total_horas = total_horas.filter(PlantaoRealizado.competencia_ano == ano)
        
        total_horas = total_horas.scalar() or 0
        
        # Total de escalas
        query_escalas = Escala.query
        
        if mes:
            query_escalas = query_escalas.filter_by(competencia_mes=mes)
        if ano:
            query_escalas = query_escalas.filter_by(competencia_ano=ano)
        
        total_escalas = query_escalas.count()
        
        # Média de horas por servidor
        media_horas = total_horas / total_servidores if total_servidores > 0 else 0
        
        return {
            'total_servidores': total_servidores,
            'total_plantoes': total_plantoes,
            'total_horas': total_horas,
            'total_horas_display': PlantaoRealizado.get_horas_display(total_horas),
            'total_escalas': total_escalas,
            'media_horas': media_horas,
            'media_horas_display': PlantaoRealizado.get_horas_display(int(media_horas))
        }
    
    @staticmethod
    def plantoes_por_mes(ano):
        """
        Retorna total de plantões e horas por mês de um ano
        
        Args:
            ano: Ano (YYYY)
            
        Returns:
            dict: Dados por mês
        """
        resultados = db.session.query(
            PlantaoRealizado.competencia_mes,
            func.count(PlantaoRealizado.id).label('total_plantoes'),
            func.sum(PlantaoRealizado.horas_trabalhadas).label('total_horas')
        ).filter(
            PlantaoRealizado.competencia_ano == ano
        ).group_by(
            PlantaoRealizado.competencia_mes
        ).all()
        
        # Criar dicionário com todos os meses (alguns podem estar vazios)
        dados_por_mes = {}
        for mes in range(1, 13):
            dados_por_mes[mes] = {
                'mes': mes,
                'total_plantoes': 0,
                'total_horas': 0
            }
        
        # Preencher com dados reais
        for r in resultados:
            dados_por_mes[r.competencia_mes] = {
                'mes': r.competencia_mes,
                'total_plantoes': r.total_plantoes,
                'total_horas': r.total_horas or 0,
                'total_horas_display': PlantaoRealizado.get_horas_display(r.total_horas or 0)
            }
        
        return dados_por_mes
    
    @staticmethod
    def servidores_mais_escalados(mes, ano, limite=10):
        """
        Retorna servidores mais escalados em um mês
        
        Args:
            mes: Mês (1-12)
            ano: Ano (YYYY)
            limite: Número de servidores
            
        Returns:
            list: Lista de servidores e quantidade de dias
        """
        # Buscar escalas do mês
        escalas = Escala.buscar_por_competencia(mes, ano).all()
        
        if not escalas:
            return []
        
        escala_ids = [e.id for e in escalas]
        
        # Contar distribuições por servidor
        resultados = db.session.query(
            Servidor.id,
            Servidor.nome_completo,
            Servidor.matricula,
            func.count(EscalaDistribuicao.id).label('total_dias')
        ).join(
            EscalaDistribuicao, Servidor.id == EscalaDistribuicao.servidor_id
        ).filter(
            EscalaDistribuicao.escala_id.in_(escala_ids)
        ).group_by(
            Servidor.id
        ).order_by(
            desc('total_dias')
        ).limit(limite).all()
        
        return [
            {
                'servidor_id': r.id,
                'nome': r.nome_completo,
                'matricula': r.matricula,
                'total_dias': r.total_dias
            }
            for r in resultados
        ]
    
    @staticmethod
    def comparativo_mensal(ano):
        """
        Retorna dados comparativos mês a mês para gráficos
        
        Args:
            ano: Ano (YYYY)
            
        Returns:
            dict: Dados formatados para gráficos
        """
        dados = Estatisticas.plantoes_por_mes(ano)
        
        meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        
        labels = []
        plantoes = []
        horas = []
        
        for mes in range(1, 13):
            labels.append(meses[mes - 1])
            plantoes.append(dados[mes]['total_plantoes'])
            horas.append(dados[mes]['total_horas'])
        
        return {
            'labels': labels,
            'plantoes': plantoes,
            'horas': horas
        }
    
    @staticmethod
    def taxa_ocupacao_mes(mes, ano):
        """
        Calcula a taxa de ocupação do mês
        (quantos % dos dias têm plantões registrados)
        
        Args:
            mes: Mês (1-12)
            ano: Ano (YYYY)
            
        Returns:
            float: Taxa de ocupação (0-100)
        """
        dias_no_mes = calendar.monthrange(ano, mes)[1]
        
        # Contar dias únicos com plantão
        dias_com_plantao = db.session.query(
            func.count(func.distinct(PlantaoRealizado.dia_mes))
        ).filter(
            PlantaoRealizado.competencia_mes == mes,
            PlantaoRealizado.competencia_ano == ano
        ).scalar() or 0
        
        taxa = (dias_com_plantao / dias_no_mes) * 100 if dias_no_mes > 0 else 0
        
        return round(taxa, 2)
    
    @staticmethod
    def resumo_servidor(servidor_id, mes, ano):
        """
        Retorna resumo completo de um servidor no mês
        
        Args:
            servidor_id: ID do servidor
            mes: Mês (1-12)
            ano: Ano (YYYY)
            
        Returns:
            dict: Resumo do servidor
        """
        servidor = Servidor.query.get(servidor_id)
        
        if not servidor:
            return None
        
        # Buscar plantões
        plantoes = PlantaoRealizado.buscar_por_servidor_e_competencia(servidor_id, mes, ano)
        
        # Calcular totais
        total_dias = len(plantoes)
        total_horas = sum(p.horas_trabalhadas or 0 for p in plantoes)
        total_noturno = sum(p.adicional_noturno or 0 for p in plantoes)
        
        return {
            'servidor': servidor.to_dict(),
            'total_dias': total_dias,
            'total_horas': total_horas,
            'total_horas_display': PlantaoRealizado.get_horas_display(total_horas),
            'total_noturno': total_noturno,
            'total_noturno_display': PlantaoRealizado.get_horas_display(total_noturno),
            'plantoes': [p.to_dict() for p in plantoes]
        }