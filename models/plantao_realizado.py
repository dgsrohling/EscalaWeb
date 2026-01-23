"""
Modelo de Plantão Realizado
"""

from datetime import datetime, time, timedelta
from utils.database import db


class PlantaoRealizado(db.Model):
    """
    Modelo de Plantão Realizado
    
    Registra os plantões efetivamente realizados pelos servidores
    
    Attributes:
        id: ID único do plantão
        servidor_id: ID do servidor
        competencia_mes: Mês da competência (1-12)
        competencia_ano: Ano da competência (YYYY)
        dia_mes: Dia do mês (1-31)
        hora_inicio: Horário de início do plantão
        hora_fim: Horário de fim do plantão
        horas_trabalhadas: Total de horas trabalhadas (em minutos)
        adicional_noturno: Horas de adicional noturno (em minutos)
        tipo_plantao: Tipo do plantão (NORMAL, FERIADO, FINAL_SEMANA)
        observacao: Observações
        registrado_em: Data e hora do registro
    """
    
    __tablename__ = 'plantoes_realizados'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relacionamento com servidor
    servidor_id = db.Column(db.Integer, db.ForeignKey('servidores.id'), nullable=False)
    
    # Competência
    competencia_mes = db.Column(db.Integer, nullable=False)  # 1-12
    competencia_ano = db.Column(db.Integer, nullable=False)  # YYYY
    dia_mes = db.Column(db.Integer, nullable=False)  # 1-31
    
    # Horários
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fim = db.Column(db.Time, nullable=False)
    
    # Horas (armazenadas em minutos para facilitar cálculos)
    horas_trabalhadas = db.Column(db.Integer, nullable=False)  # minutos
    adicional_noturno = db.Column(db.Integer, default=0)  # minutos
    
    # Tipo de plantão
    tipo_plantao = db.Column(db.String(20), default='NORMAL')
    # tipo_plantao: 'NORMAL', 'FERIADO', 'FINAL_SEMANA'
    
    # Observações
    observacao = db.Column(db.Text)
    
    # Timestamp
    registrado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relacionamentos
    servidor = db.relationship('Servidor', back_populates='plantoes_realizados')
    
    # Índices para busca rápida
    __table_args__ = (
        db.UniqueConstraint('servidor_id', 'competencia_mes', 'competencia_ano', 'dia_mes', 
                          name='uq_servidor_competencia_dia'),
        db.Index('idx_competencia', 'competencia_mes', 'competencia_ano'),
    )
    
    def __repr__(self):
        return f'<PlantaoRealizado Servidor={self.servidor_id} {self.dia_mes}/{self.competencia_mes}/{self.competencia_ano}>'
    
    def to_dict(self):
        """
        Converte o plantão para dicionário
        
        Returns:
            dict: Dados do plantão
        """
        return {
            'id': self.id,
            'servidor_id': self.servidor_id,
            'servidor_nome': self.servidor.nome_completo if self.servidor else None,
            'servidor_matricula': self.servidor.matricula if self.servidor else None,
            'competencia_mes': self.competencia_mes,
            'competencia_ano': self.competencia_ano,
            'dia_mes': self.dia_mes,
            'data_completa': f'{self.dia_mes:02d}/{self.competencia_mes:02d}/{self.competencia_ano}',
            'hora_inicio': self.hora_inicio.strftime('%H:%M') if self.hora_inicio else None,
            'hora_fim': self.hora_fim.strftime('%H:%M') if self.hora_fim else None,
            'horas_trabalhadas': self.horas_trabalhadas,
            'horas_trabalhadas_display': self.get_horas_display(self.horas_trabalhadas),
            'adicional_noturno': self.adicional_noturno,
            'adicional_noturno_display': self.get_horas_display(self.adicional_noturno),
            'tipo_plantao': self.tipo_plantao,
            'observacao': self.observacao,
            'registrado_em': self.registrado_em.isoformat() if self.registrado_em else None
        }
    
    @staticmethod
    def get_horas_display(minutos):
        """
        Converte minutos para formato HH:MM
        
        Args:
            minutos: Total de minutos
            
        Returns:
            str: Formato HH:MM
        """
        if not minutos:
            return '00:00'
        
        horas = minutos // 60
        mins = minutos % 60
        return f'{horas:02d}:{mins:02d}'
    
    @staticmethod
    def calcular_horas_trabalhadas(hora_inicio, hora_fim):
        """
        Calcula o total de horas trabalhadas entre dois horários
        
        Args:
            hora_inicio: time object
            hora_fim: time object
            
        Returns:
            int: Total de minutos trabalhados
        """
        # Converter time para datetime para facilitar cálculo
        inicio = datetime.combine(datetime.today(), hora_inicio)
        fim = datetime.combine(datetime.today(), hora_fim)
        
        # Se fim < início, significa que passou da meia-noite
        if fim < inicio:
            fim += timedelta(days=1)
        
        diferenca = fim - inicio
        return int(diferenca.total_seconds() / 60)
    
    @staticmethod
    def calcular_adicional_noturno(hora_inicio, hora_fim):
        """
        Calcula o adicional noturno (22h às 05h)
        
        Args:
            hora_inicio: time object
            hora_fim: time object
            
        Returns:
            int: Total de minutos de adicional noturno
        """
        # Horário noturno: 22:00 às 05:00
        noturno_inicio = time(22, 0)
        noturno_fim = time(5, 0)
        
        inicio = datetime.combine(datetime.today(), hora_inicio)
        fim = datetime.combine(datetime.today(), hora_fim)
        
        # Se fim < início, passou da meia-noite
        if fim < inicio:
            fim += timedelta(days=1)
        
        # Criar intervalos de período noturno
        noturno_inicio_dt = datetime.combine(datetime.today(), noturno_inicio)
        noturno_fim_dt = datetime.combine(datetime.today() + timedelta(days=1), noturno_fim)
        
        # Calcular interseção
        overlap_inicio = max(inicio, noturno_inicio_dt)
        overlap_fim = min(fim, noturno_fim_dt)
        
        if overlap_fim > overlap_inicio:
            diferenca = overlap_fim - overlap_inicio
            return int(diferenca.total_seconds() / 60)
        
        return 0
    
    @staticmethod
    def buscar_por_servidor_e_competencia(servidor_id, mes, ano):
        """
        Busca plantões de um servidor em uma competência
        
        Args:
            servidor_id: ID do servidor
            mes: Mês (1-12)
            ano: Ano (YYYY)
            
        Returns:
            list: Lista de PlantaoRealizado
        """
        return PlantaoRealizado.query.filter_by(
            servidor_id=servidor_id,
            competencia_mes=mes,
            competencia_ano=ano
        ).order_by(PlantaoRealizado.dia_mes).all()
    
    @staticmethod
    def total_horas_servidor_mes(servidor_id, mes, ano):
        """
        Calcula o total de horas de um servidor no mês
        
        Args:
            servidor_id: ID do servidor
            mes: Mês (1-12)
            ano: Ano (YYYY)
            
        Returns:
            dict: {'horas_trabalhadas': int, 'adicional_noturno': int}
        """
        plantoes = PlantaoRealizado.buscar_por_servidor_e_competencia(servidor_id, mes, ano)
        
        total_horas = sum(p.horas_trabalhadas or 0 for p in plantoes)
        total_noturno = sum(p.adicional_noturno or 0 for p in plantoes)
        
        return {
            'horas_trabalhadas': total_horas,
            'adicional_noturno': total_noturno
        }
    
    @staticmethod
    def verificar_existencia(servidor_id, mes, ano, dia):
        """
        Verifica se já existe plantão registrado para o servidor neste dia
        
        Args:
            servidor_id: ID do servidor
            mes: Mês (1-12)
            ano: Ano (YYYY)
            dia: Dia do mês (1-31)
            
        Returns:
            bool: True se já existe
        """
        return PlantaoRealizado.query.filter_by(
            servidor_id=servidor_id,
            competencia_mes=mes,
            competencia_ano=ano,
            dia_mes=dia
        ).first() is not None