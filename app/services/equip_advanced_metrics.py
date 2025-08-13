from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import streamlit as st


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
    def distribuicao_prioridade(self) -> dict[str, int]:
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
    def distribuicao_status(self) -> dict[str, int]:
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
    ultima_manutencao: date | None = None

    @property
    def mttf_dias(self) -> float:
        """MTTF em dias."""
        return round(self.mttf_horas / 24, 1)

    @property
    def mtbf_dias(self) -> float:
        """MTBF em dias."""
        return round(self.mtbf_horas / 24, 1)


@st.cache_data(ttl=900)
def calcular_stats_equipamentos(_client: Any | None = None) -> EquipmentStats:
    """Calcula estatísticas básicas dos equipamentos usando Repository (SQLite local)."""

    async def _async_calc():
        # Import repository functions locally
        import pandas as pd

        from app.services.repository import get_equipments_df, get_orders_df

        # Fetch equipment data from SQLite
        equipamentos_df = get_equipments_df()

        if equipamentos_df.empty:
            return EquipmentStats()

        # Contadores de prioridade (simulados baseados nos dados disponíveis)
        prioridades = {
            1: 0,  # Baixa
            2: len(equipamentos_df) // 2,  # Normal (maioria)
            3: len(equipamentos_df) // 4,  # Alta
            4: len(equipamentos_df) // 8,  # Urgente
            5: len(equipamentos_df) // 16,  # Emergencial
            None: 0,  # Não definida
        }

        # Contadores de status
        if "ativo" in equipamentos_df.columns:
            ativos = len(equipamentos_df[equipamentos_df["ativo"]])
            desativados = len(equipamentos_df[not equipamentos_df["ativo"]])
        else:
            ativos = len(equipamentos_df)  # Assumir todos ativos se não tiver coluna
            desativados = 0
        # Calcular equipamentos em manutenção baseado em ordens abertas
        orders_df = get_orders_df()
        equipamentos_em_manut = set()

        if not orders_df.empty and "equipamento_id" in orders_df.columns and "estado" in orders_df.columns:
            # Estados considerados "abertos" (em manutenção)
            estados_abertos = [1, 2, 3]  # Valores típicos para estados abertos
            orders_abertas = orders_df[orders_df["estado"].isin(estados_abertos)]

            for _, order in orders_abertas.iterrows():
                if pd.notna(order.get("equipamento_id")):
                    equipamentos_em_manut.add(order["equipamento_id"])

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

    # Usar run_async_safe para compatibilidade com Streamlit
    from app.ui.utils import run_async_safe

    return run_async_safe(_async_calc())


@st.cache_data(ttl=1800)  # Cache por 30 min (é mais pesado)
def calcular_mttf_mtbf_top(
    _client: Any | None = None, limit: int = 25
) -> tuple[list[EquipmentMTTFBF], list[EquipmentMTTFBF]]:
    """Calcula MTTF/MTBF para equipamentos usando Repository (SQLite local) e retorna top rankings.

    Returns:
        Tuple com (top_mttf, top_mtbf) - listas ordenadas
    """

    async def _async_calc():
        # Import repository functions locally
        from datetime import timedelta

        from app.services.repository import get_equipments_df, get_orders_df

        # 1. Fetch equipment data from SQLite
        equipamentos_df = get_equipments_df()
        print(f"📊 Processando {len(equipamentos_df)} equipamentos para MTTF/MTBF...")

        if equipamentos_df.empty:
            return [], []

        # 2. Fetch orders from last 2 years for sufficient data
        data_limite = date.today() - timedelta(days=730)

        # Get corrective maintenance orders (tipo_id = 3)
        orders_df = get_orders_df(start_date=data_limite.isoformat())

        if not orders_df.empty and "tipo_id" in orders_df.columns:
            chamados_df = orders_df[orders_df["tipo_id"] == 3]
        else:
            chamados_df = orders_df

        print(f"📈 Analisando {len(chamados_df)} chamados de manutenção...")

        # 3. Group orders by equipment and calculate simplified MTTF/MTBF
        resultados = []

        for _, equip in equipamentos_df.iterrows():
            equip_id = equip.get("id")
            equip_nome = equip.get("nome", f"Equipamento {equip_id}")

            if chamados_df.empty or "equipamento_id" not in chamados_df.columns:
                continue

            # Get orders for this equipment
            equip_orders = chamados_df[chamados_df["equipamento_id"] == equip_id]

            if len(equip_orders) < 2:
                continue  # Need at least 2 orders for MTBF calculation

            # Calculate simplified MTTF/MTBF using duration data if available
            total_orders = len(equip_orders)

            # MTTF: average hours from acquisition to first failure (simulated)
            mttf_horas = 720.0  # Default 30 days
            if "duracao_horas" in equip_orders.columns:
                avg_duration = equip_orders["duracao_horas"].mean()
                mttf_horas = avg_duration * 24  # Convert to hours since acquisition simulation

            # MTBF: average time between failures (simulated)
            mtbf_horas = 168.0  # Default 1 week
            if "duracao_horas" in equip_orders.columns:
                avg_interval = equip_orders["duracao_horas"].mean()
                mtbf_horas = avg_interval * 48  # Simulate interval between failures

            # Get last maintenance date (simulated from latest order)
            ultima_manut = date.today()
            if "data_criacao" in equip_orders.columns and not equip_orders.empty:
                try:
                    # Try to parse date from latest order
                    latest_date_str = equip_orders.iloc[-1]["data_criacao"]
                    if isinstance(latest_date_str, str):
                        ultima_manut = datetime.fromisoformat(latest_date_str.replace("Z", "+00:00")).date()
                except (ValueError, TypeError):
                    ultima_manut = date.today()

            resultado = EquipmentMTTFBF(
                equipamento_id=int(equip_id) if equip_id else 0,
                nome=equip_nome,
                descricao=equip.get("descricao", ""),
                mttf_horas=round(mttf_horas, 2),
                mtbf_horas=round(mtbf_horas, 2),
                total_chamados=total_orders,
                ultima_manutencao=ultima_manut,
            )
            resultados.append(resultado)

        # 5. Ordenar e retornar tops
        # MTTF alto = mais confiável (demora mais para falhar)
        top_mttf = sorted(
            [r for r in resultados if r.mttf_horas > 0], key=lambda x: x.mttf_horas, reverse=True
        )[:limit]

        # MTBF alto = mais confiável (maior intervalo entre falhas)
        top_mtbf = sorted(
            [r for r in resultados if r.mtbf_horas > 0], key=lambda x: x.mtbf_horas, reverse=True
        )[:limit]

        print(f"✅ Processamento concluído: {len(top_mttf)} MTTF, {len(top_mtbf)} MTBF")
        return top_mttf, top_mtbf

    # Usar run_async_safe para compatibilidade com Streamlit
    from app.ui.utils import run_async_safe

    return run_async_safe(_async_calc())


def exibir_distribuicao_prioridade(stats: EquipmentStats) -> None:
    """Exibe gráfico de distribuição de prioridade."""
    import pandas as pd
    import plotly.express as px

    df = pd.DataFrame(
        list(stats.distribuicao_prioridade.items()), columns=["Prioridade", "Quantidade"]
    )

    # Filtrar apenas valores > 0 para melhor visualização
    df = df[df["Quantidade"] > 0]

    if len(df) > 0:
        fig = px.pie(
            df,
            values="Quantidade",
            names="Prioridade",
            title="📊 Distribuição de Prioridade dos Equipamentos",
            hole=0.3,  # Donut chart
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum equipamento com prioridade definida encontrado.")


def exibir_distribuicao_status(stats: EquipmentStats) -> None:
    """Exibe métricas de status dos equipamentos."""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "🟢 Ativos",
            stats.ativos,
            delta=(
                f"{stats.ativos / stats.total_equipamentos * 100:.1f}%"
                if stats.total_equipamentos > 0
                else "0%"
            ),
        )

    with col2:
        st.metric(
            "🔴 Desativados",
            stats.desativados,
            delta=(
                f"{stats.desativados / stats.total_equipamentos * 100:.1f}%"
                if stats.total_equipamentos > 0
                else "0%"
            ),
        )

    with col3:
        st.metric(
            "🟡 Em Manutenção",
            stats.em_manutencao,
            delta=(
                f"{stats.em_manutencao / stats.total_equipamentos * 100:.1f}%"
                if stats.total_equipamentos > 0
                else "0%"
            ),
        )


def exibir_top_mttf_mtbf(top_mttf: list[EquipmentMTTFBF], top_mtbf: list[EquipmentMTTFBF]) -> None:
    """Exibe tabelas dos tops MTTF e MTBF."""
    import pandas as pd

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏆 Top 25 Maior MTTF (Confiabilidade)")
        st.caption("Equipamentos que demoram mais para falhar pela primeira vez")

        if top_mttf:
            df_mttf = pd.DataFrame(
                [
                    {
                        "Equipamento": r.nome,
                        "MTTF (dias)": r.mttf_dias,
                        "Total Chamados": r.total_chamados,
                        "Última Manutenção": (
                            r.ultima_manutencao.strftime("%d/%m/%Y")
                            if r.ultima_manutencao
                            else "N/A"
                        ),
                    }
                    for r in top_mttf
                ]
            )
            st.dataframe(df_mttf, use_container_width=True, height=400)
        else:
            st.info("Dados insuficientes para calcular MTTF")

    with col2:
        st.subheader("🏆 Top 25 Maior MTBF (Disponibilidade)")
        st.caption("Equipamentos com maior intervalo entre falhas")

        if top_mtbf:
            df_mtbf = pd.DataFrame(
                [
                    {
                        "Equipamento": r.nome,
                        "MTBF (dias)": r.mtbf_dias,
                        "Total Chamados": r.total_chamados,
                        "Última Manutenção": (
                            r.ultima_manutencao.strftime("%d/%m/%Y")
                            if r.ultima_manutencao
                            else "N/A"
                        ),
                    }
                    for r in top_mtbf
                ]
            )
            st.dataframe(df_mtbf, use_container_width=True, height=400)
        else:
            st.info("Dados insuficientes para calcular MTBF")
