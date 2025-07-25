from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from statistics import mean
from typing import Any, Dict, List, Optional

import streamlit as st
from arkmeds_client.client import ArkmedsClient
from arkmeds_client.models import Equipment, Chamado, OSEstado


@dataclass(frozen=True)
class EquipmentStats:
    """Estatísticas avançadas de equipamentos."""
    
    # Distribuição de prioridades
    prioridade_baixa: int = 0
    prioridade_normal: int = 0
    prioridade_alta: int = 0
    prioridade_urgente: int = 0
    prioridade_emergencial: int = 0
    prioridade_nao_definida: int = 0
    
    # Status dos equipamentos
    ativos: int = 0
    desativados: int = 0
    em_manutencao: int = 0
    
    @property
    def total_equipamentos(self) -> int:
        """Total de equipamentos."""
        return self.ativos + self.desativados + self.em_manutencao
    
    @property
    def distribuicao_prioridade(self) -> Dict[str, int]:
        """Retorna distribuição de prioridade como dict."""
        return {
            "Baixa": self.prioridade_baixa,
            "Normal": self.prioridade_normal,
            "Alta": self.prioridade_alta,
            "Urgente": self.prioridade_urgente,
            "Emergencial": self.prioridade_emergencial,
            "Não definida": self.prioridade_nao_definida,
        }
    
    @property
    def distribuicao_status(self) -> Dict[str, int]:
        """Retorna distribuição de status como dict."""
        return {
            "Ativos": self.ativos,
            "Desativados": self.desativados,
            "Em manutenção": self.em_manutencao,
        }


@dataclass(frozen=True)
class EquipmentMTTFBF:
    """Dados de MTTF/MTBF para um equipamento."""
    
    equipamento_id: int
    nome: str
    descricao: str
    mttf_horas: float  # Mean Time To Failure
    mtbf_horas: float  # Mean Time Between Failures
    total_chamados: int
    ultima_manutencao: Optional[date] = None
    
    @property
    def mttf_dias(self) -> float:
        """MTTF em dias."""
        return round(self.mttf_horas / 24, 1)
    
    @property
    def mtbf_dias(self) -> float:
        """MTBF em dias.""" 
        return round(self.mtbf_horas / 24, 1)


@st.cache_data(ttl=900)
def calcular_stats_equipamentos(_client: ArkmedsClient) -> EquipmentStats:
    """Calcula estatísticas básicas dos equipamentos."""
    
    async def _async_calc():
        # Usar o método correto para buscar equipamentos
        equipamentos = await _client.list_equipamentos()
        
        # Contadores de prioridade
        prioridades = {
            1: 0,  # Baixa
            2: 0,  # Normal
            3: 0,  # Alta
            4: 0,  # Urgente
            5: 0,  # Emergencial
            None: 0,  # Não definida
        }
        
        # Contadores de status
        ativos = 0
        desativados = 0
        
        for equip in equipamentos:
            # Contar prioridades
            prioridade = equip.prioridade
            if prioridade in prioridades:
                prioridades[prioridade] += 1
            else:
                prioridades[None] += 1
            
            # Contar status (assumindo que 'ativo' existe no modelo)
            if getattr(equip, 'ativo', True):  # Default True se não existir
                ativos += 1
            else:
                desativados += 1
        
        # Para em_manutencao, precisamos verificar chamados abertos
        chamados_abertos = await _client.list_chamados({
            "estado__in": [e.value for e in OSEstado.estados_abertos()]
        })
        
        equipamentos_em_manut = set()
        for chamado in chamados_abertos:
            if chamado.equipamento_id:
                equipamentos_em_manut.add(chamado.equipamento_id)
        
        return EquipmentStats(
            prioridade_baixa=prioridades[1],
            prioridade_normal=prioridades[2], 
            prioridade_alta=prioridades[3],
            prioridade_urgente=prioridades[4],
            prioridade_emergencial=prioridades[5],
            prioridade_nao_definida=prioridades[None],
            ativos=ativos,
            desativados=desativados,
            em_manutencao=len(equipamentos_em_manut),
        )
    
    return asyncio.run(_async_calc())


@st.cache_data(ttl=1800)  # Cache por 30 min (é mais pesado)
def calcular_mttf_mtbf_top(_client: ArkmedsClient, limit: int = 25) -> tuple[List[EquipmentMTTFBF], List[EquipmentMTTFBF]]:
    """Calcula MTTF/MTBF para equipamentos e retorna top rankings.
    
    Returns:
        Tuple com (top_mttf, top_mtbf) - listas ordenadas
    """
    
    async def _async_calc():
        # 1. Buscar todos os equipamentos - usar método correto
        equipamentos = await _client.list_equipamentos()
        print(f"📊 Processando {len(equipamentos)} equipamentos para MTTF/MTBF...")
        
        # 2. Buscar chamados dos últimos 2 anos para ter dados suficientes
        from datetime import timedelta
        data_limite = date.today() - timedelta(days=730)
        
        chamados = await _client.list_chamados({
            "data_criacao__gte": data_limite,
            "tipo_id": 3  # Apenas manutenções corretivas
        })
        
        print(f"📈 Analisando {len(chamados)} chamados de manutenção...")
        
        # 3. Agrupar chamados por equipamento
        chamados_por_equip = defaultdict(list)
        for chamado in chamados:
            if chamado.equipamento_id:
                chamados_por_equip[chamado.equipamento_id].append(chamado)
        
        # 4. Calcular MTTF/MTBF para cada equipamento
        resultados = []
        
        for equip in equipamentos:
            if equip.id not in chamados_por_equip:
                continue  # Sem dados de chamados
                
            chamados_equip = sorted(
                chamados_por_equip[equip.id],
                key=lambda c: datetime.strptime(c.data_criacao_os, "%d/%m/%y - %H:%M")
            )
            
            if len(chamados_equip) < 2:
                continue  # Precisa de pelo menos 2 chamados
            
            # Calcular MTTF (tempo até primeira falha após aquisição)
            mttf_horas = 0.0
            if equip.data_aquisicao:
                primeiro_chamado = datetime.strptime(
                    chamados_equip[0].data_criacao_os, "%d/%m/%y - %H:%M"
                )
                mttf_horas = (primeiro_chamado - equip.data_aquisicao).total_seconds() / 3600
            
            # Calcular MTBF (tempo médio entre falhas)
            intervalos = []
            for i in range(1, len(chamados_equip)):
                data_atual = datetime.strptime(
                    chamados_equip[i].data_criacao_os, "%d/%m/%y - %H:%M"
                )
                data_anterior = datetime.strptime(
                    chamados_equip[i-1].data_criacao_os, "%d/%m/%y - %H:%M"
                )
                intervalo = (data_atual - data_anterior).total_seconds() / 3600
                intervalos.append(intervalo)
            
            mtbf_horas = mean(intervalos) if intervalos else 0.0
            
            # Data da última manutenção
            ultima_manut = datetime.strptime(
                chamados_equip[-1].data_criacao_os, "%d/%m/%y - %H:%M"
            ).date()
            
            resultado = EquipmentMTTFBF(
                equipamento_id=equip.id,
                nome=equip.display_name,
                descricao=equip.descricao_completa,
                mttf_horas=round(mttf_horas, 2),
                mtbf_horas=round(mtbf_horas, 2),
                total_chamados=len(chamados_equip),
                ultima_manutencao=ultima_manut,
            )
            resultados.append(resultado)
        
        # 5. Ordenar e retornar tops
        # MTTF alto = mais confiável (demora mais para falhar)
        top_mttf = sorted(
            [r for r in resultados if r.mttf_horas > 0],
            key=lambda x: x.mttf_horas,
            reverse=True
        )[:limit]
        
        # MTBF alto = mais confiável (maior intervalo entre falhas)  
        top_mtbf = sorted(
            [r for r in resultados if r.mtbf_horas > 0],
            key=lambda x: x.mtbf_horas,
            reverse=True
        )[:limit]
        
        print(f"✅ Processamento concluído: {len(top_mttf)} MTTF, {len(top_mtbf)} MTBF")
        return top_mttf, top_mtbf
    
    return asyncio.run(_async_calc())


def exibir_distribuicao_prioridade(stats: EquipmentStats):
    """Exibe gráfico de distribuição de prioridade."""
    import plotly.express as px
    import pandas as pd
    
    df = pd.DataFrame(
        list(stats.distribuicao_prioridade.items()),
        columns=['Prioridade', 'Quantidade']
    )
    
    # Filtrar apenas valores > 0 para melhor visualização
    df = df[df['Quantidade'] > 0]
    
    if len(df) > 0:
        fig = px.pie(
            df, 
            values='Quantidade', 
            names='Prioridade',
            title="📊 Distribuição de Prioridade dos Equipamentos",
            hole=0.3  # Donut chart
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum equipamento com prioridade definida encontrado.")


def exibir_distribuicao_status(stats: EquipmentStats):
    """Exibe métricas de status dos equipamentos."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "🟢 Ativos", 
            stats.ativos,
            delta=f"{stats.ativos / stats.total_equipamentos * 100:.1f}%" if stats.total_equipamentos > 0 else "0%"
        )
    
    with col2:
        st.metric(
            "🔴 Desativados", 
            stats.desativados,
            delta=f"{stats.desativados / stats.total_equipamentos * 100:.1f}%" if stats.total_equipamentos > 0 else "0%"
        )
    
    with col3:
        st.metric(
            "🟡 Em Manutenção", 
            stats.em_manutencao,
            delta=f"{stats.em_manutencao / stats.total_equipamentos * 100:.1f}%" if stats.total_equipamentos > 0 else "0%"
        )


def exibir_top_mttf_mtbf(top_mttf: List[EquipmentMTTFBF], top_mtbf: List[EquipmentMTTFBF]):
    """Exibe tabelas dos tops MTTF e MTBF."""
    import pandas as pd
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top 25 Maior MTTF (Confiabilidade)")
        st.caption("Equipamentos que demoram mais para falhar pela primeira vez")
        
        if top_mttf:
            df_mttf = pd.DataFrame([
                {
                    "Equipamento": r.nome,
                    "MTTF (dias)": r.mttf_dias,
                    "Total Chamados": r.total_chamados,
                    "Última Manutenção": r.ultima_manutencao.strftime("%d/%m/%Y") if r.ultima_manutencao else "N/A"
                }
                for r in top_mttf
            ])
            st.dataframe(df_mttf, use_container_width=True, height=400)
        else:
            st.info("Dados insuficientes para calcular MTTF")
    
    with col2:
        st.subheader("🏆 Top 25 Maior MTBF (Disponibilidade)")
        st.caption("Equipamentos com maior intervalo entre falhas")
        
        if top_mtbf:
            df_mtbf = pd.DataFrame([
                {
                    "Equipamento": r.nome,
                    "MTBF (dias)": r.mtbf_dias,
                    "Total Chamados": r.total_chamados,
                    "Última Manutenção": r.ultima_manutencao.strftime("%d/%m/%Y") if r.ultima_manutencao else "N/A"
                }
                for r in top_mtbf
            ])
            st.dataframe(df_mtbf, use_container_width=True, height=400)
        else:
            st.info("Dados insuficientes para calcular MTBF")
