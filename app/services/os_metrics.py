from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, cast

import httpx
import pandas as pd
import streamlit as st

from app.arkmeds_client.auth import ArkmedsAuthError
from app.arkmeds_client.client import ArkmedsClient
from app.arkmeds_client.models import Chamado, OSEstado
from app.config.os_types import (
    AREA_ENG_CLIN,
    AREA_PREDIAL,
    TIPO_BUSCA_ATIVA,
    TIPO_CORRETIVA,
    TIPO_PREVENTIVA,
)
from app.services.sync.delta import run_incremental_sync, should_run_incremental_sync


# Type aliases
ServiceOrderData = dict[str, list[Chamado]]

SLA_HOURS = int(os.getenv("OS_SLA_HOURS", 72))


class OSMetricsError(Exception):
    """Base exception for service order metrics related errors."""

    pass


class DataFetchError(OSMetricsError):
    """Raised when there's an error fetching data from the API."""

    pass


class ValidationError(OSMetricsError):
    """Raised when input validation fails."""

    pass


@dataclass(frozen=True)
class OSMetrics:
    """Represents comprehensive metrics for service orders analysis.

    Attributes:
        corrective_building: Number of corrective orders for building maintenance
        corrective_engineering: Number of corrective orders for clinical engineering
        preventive_building: Number of preventive orders for building maintenance
        preventive_infra: Number of preventive orders for infrastructure
        active_search: Number of active search orders
        backlog: Current backlog (open orders - closed orders)
        sla_percentage: Percentage of orders closed within SLA (0-100)
    """

    corrective_building: int
    corrective_engineering: int
    preventive_building: int
    preventive_infra: int
    active_search: int
    backlog: int
    sla_percentage: float

    # Compatibility aliases
    @property
    def corretivas_predial(self) -> int:
        return self.corrective_building

    @property
    def corretivas_engenharia(self) -> int:
        return self.corrective_engineering

    @property
    def preventivas_predial(self) -> int:
        return self.preventive_building

    @property
    def preventivas_infra(self) -> int:
        return self.preventive_infra

    @property
    def busca_ativa(self) -> int:
        return self.active_search

    @property
    def sla_pct(self) -> float:
        return self.sla_percentage


def _validate_dates(start_date: date, end_date: date) -> None:
    """Validate date range parameters.

    Args:
        start_date: Start date of the period
        end_date: End date of the period

    Raises:
        ValidationError: If dates are invalid
    """
    if not isinstance(start_date, date) or not isinstance(end_date, date):
        raise ValidationError("Both start_date and end_date must be date objects")

    if start_date > end_date:
        raise ValidationError("start_date cannot be after end_date")

    if start_date < date(2020, 1, 1):
        raise ValidationError("start_date is too far in the past")

    if end_date > date.today() + timedelta(days=30):
        raise ValidationError("end_date cannot be more than 30 days in the future")


async def fetch_orders(
    client: ArkmedsClient, order_type: int, area_id: int | None = None, **extra: Any
) -> list[Chamado]:
    """Fetch orders from the API with the given filters.

    Args:
        client: The Arkmeds API client
        order_type: Type of order to fetch
        area_id: Optional area ID to filter by
        **extra: Additional filters

    Returns:
        List of service orders
    """
    params: dict[str, Any] = {
        **extra,
    }

    if area_id is not None:
        params["area_id"] = area_id
        params["area_id"] = area_id

    # Nota: O parâmetro tipo_id não é suportado pela API atual
    # A filtragem por tipo deve ser feita após receber os dados
    return await client.list_chamados(params)


async def fetch_service_orders_with_cache(
    client: ArkmedsClient, start_date: date, end_date: date, **filters: Any
) -> ServiceOrderData:
    """
    Fetch service orders data usando SQLite como fonte primária.

    🔄 REFATORADO PARA LEITURA DIRETA DO SQLITE

    Prioridade de busca:
    1. SQLite local (dados frescos e rápidos)
    2. Auto-sync incremental se dados desatualizados
    3. Fallback para API apenas se necessário

    Args:
        client: The Arkmeds API client instance (mantido para compatibilidade)
        start_date: Start date for the query (inclusive)
        end_date: End date for the query (inclusive)
        **filters: Additional filters to apply to all queries

    Returns:
        Dictionary containing categorized lists of service orders

    Raises:
        DataFetchError: If there's an error fetching data
        ValidationError: If input parameters are invalid
    """
    _validate_dates(start_date, end_date)

    # ========== NOVA ABORDAGEM: LEITURA DIRETA DO SQLITE ==========
    from app.services.repository import get_database_stats, get_orders_df

    # Extrair filtros
    estado_ids = filters.get("estado_ids", [])

    try:
        # Verificar estado do banco antes de usar
        stats = get_database_stats()
        orders_count = stats.get("orders_count", 0)

        if orders_count == 0:
            st.warning("📭 Banco local vazio. Executando backfill inicial...")
            from app.services.sync.ingest import BackfillSync

            backfill = BackfillSync()
            try:
                await backfill.run_backfill(["orders"], batch_size=100)
                st.success("✅ Backfill inicial concluído")
            except Exception as e:
                st.warning(f"⚠️ Falha no backfill: {e}")
                st.info("🔄 Usando fallback para API...")
                return await fetch_service_orders(client, start_date, end_date, **filters)

        # Verificar frescor dos dados e sincronizar se necessário
        elif should_run_incremental_sync("orders", max_age_hours=2):
            try:
                st.info("🔄 Executando sincronização incremental...")
                sync_results = await run_incremental_sync(client, ["orders"], **filters)

                if sync_results.get("orders", 0) > 0:
                    st.success(f"📥 Sincronizados {sync_results['orders']:,} novos registros")
                else:
                    st.info("✅ Dados já estão atualizados")

            except Exception as e:
                st.warning(f"⚠️ Erro na sincronização incremental: {e}")
                # Continuar com dados locais existentes

        # ========== BUSCAR DO SQLITE COM FILTROS OTIMIZADOS ==========
        st.info("💾 Carregando dados do SQLite local...")

        # Converter datas para formato ISO
        start_date_str = start_date.isoformat()
        end_date_str = end_date.isoformat()

        # Usar nova função otimizada do repository
        df = get_orders_df(
            start_date=start_date_str,
            end_date=end_date_str,
            estados=estado_ids,
            limit=10000,  # Limite alto para não truncar
        )

        if df.empty:
            st.warning("� Nenhuma ordem encontrada no período especificado")
            st.info("🔄 Tentando fallback para API...")
            return await fetch_service_orders(client, start_date, end_date, **filters)

        st.success(f"✅ {len(df):,} registros carregados do SQLite local")

        # ========== CONVERTER PARA FORMATO LEGACY ==========
        # Usar nova função otimizada para converter SQLite DataFrame
        try:
            orders_data = _convert_sqlite_df_to_service_orders(df, start_date, end_date, filters)
            return orders_data
        except Exception as e:
            st.error(f"❌ Erro na conversão otimizada: {e}")
            # Fallback para conversão antiga
            return _convert_df_to_service_orders(df, start_date, end_date, filters)

    except Exception as e:
        st.error(f"❌ Erro ao buscar dados do SQLite: {e}")
        st.info("🔄 Tentando fallback para API...")

        # Fallback original para API
        orders_data = await fetch_service_orders(client, start_date, end_date, **filters)

        # Tentar salvar dados para cache futuro
        try:
            all_orders = []
            for order_list in orders_data.values():
                if isinstance(order_list, list):
                    all_orders.extend(order_list)

            if all_orders:
                from app.core.db import get_conn
                from app.services.sync._upsert import upsert_records

                # Converter para formato de payload
                orders_dict = [order.model_dump() for order in all_orders]

                with get_conn() as conn:
                    saved_count = upsert_records(conn, "orders", orders_dict)
                    st.success(f"💾 Cache atualizado: {saved_count:,} ordens salvas")

        except Exception as cache_error:
            st.warning(f"⚠️ Erro ao salvar cache: {cache_error}")

        return orders_data


def _convert_df_to_service_orders(
    df, start_date: date, end_date: date, filters: dict
) -> ServiceOrderData:
    """Convert DataFrame from database back to ServiceOrderData format.

    This function filters and categorizes the database orders to match
    the expected return format of fetch_service_orders.
    """
    import json
    from datetime import datetime

    # Convert DataFrame to Chamado objects
    orders = []
    for _, row in df.iterrows():
        try:
            # Parse ordem_servico JSON field
            os_data = (
                json.loads(row["ordem_servico"])
                if isinstance(row["ordem_servico"], str)
                else row["ordem_servico"]
            )

            # Create Chamado object
            chamado_data = {
                "id": row["id"],
                "chamados": row["chamados"],
                "data_criacao": row["data_criacao"],
                "ordem_servico": os_data,
                "responsavel_id": row["responsavel_id"],
            }

            # Add optional fields if they exist
            if pd.notna(row.get("data_fechamento")):
                chamado_data["data_fechamento"] = row["data_fechamento"]

            order = Chamado.model_validate(chamado_data)
            orders.append(order)

        except Exception:
            # Skip invalid records
            continue

    # Filter orders by date range
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    date_filtered_orders = []
    for order in orders:
        try:
            if order.data_criacao:
                if isinstance(order.data_criacao, str):
                    order_date = datetime.fromisoformat(order.data_criacao.replace("Z", "+00:00"))
                else:
                    order_date = order.data_criacao

                if start_datetime <= order_date <= end_datetime:
                    date_filtered_orders.append(order)
        except:
            continue

    # Categorize orders based on type and area
    categorized = {
        "corrective_building": [],
        "corrective_engineering": [],
        "preventive_building": [],
        "preventive_infra": [],
        "active_search": [],
        "open_orders": [],
        "closed_orders": [],
        "closed_in_period": [],
    }

    for order in orders:  # Use all orders for backlog calculations
        try:
            os = order.ordem_servico
            if not os:
                continue

            tipo_servico = os.get("tipo_servico")
            area_id = os.get("area_id")  # Assuming area_id is in ordem_servico
            estado = os.get("estado")

            # Categorize by type and area (for date-filtered orders)
            if order in date_filtered_orders:
                if tipo_servico == TIPO_CORRETIVA:
                    if area_id == AREA_PREDIAL:
                        categorized["corrective_building"].append(order)
                    elif area_id == AREA_ENG_CLIN:
                        categorized["corrective_engineering"].append(order)
                elif tipo_servico == TIPO_PREVENTIVA:
                    if area_id == AREA_PREDIAL:
                        categorized["preventive_building"].append(order)
                    elif area_id == AREA_ENG_CLIN:
                        categorized["preventive_infra"].append(order)
                elif tipo_servico == TIPO_BUSCA_ATIVA:
                    categorized["active_search"].append(order)

            # Categorize by status (all orders for backlog)
            if tipo_servico == TIPO_CORRETIVA:
                if estado == OSEstado.ABERTA.value:
                    categorized["open_orders"].append(order)
                elif estado == OSEstado.FECHADA.value:
                    categorized["closed_orders"].append(order)

                    # Check if closed in period
                    if order.data_fechamento and order in date_filtered_orders:
                        categorized["closed_in_period"].append(order)

        except Exception:
            continue

    return categorized


def _convert_sqlite_df_to_service_orders(
    df: pd.DataFrame, start_date: date, end_date: date, filters: dict
) -> ServiceOrderData:
    """
    Converte DataFrame otimizado do SQLite para ServiceOrderData.

    🚀 NOVA FUNÇÃO OTIMIZADA PARA SQLITE

    Esta função trabalha com o DataFrame já pré-processado do repository,
    eliminando parsing JSON desnecessário e melhorando performance.

    Args:
        df: DataFrame do get_orders_df() (já com colunas extraídas)
        start_date: Data inicial do filtro
        end_date: Data final do filtro
        filters: Filtros adicionais

    Returns:
        ServiceOrderData categorizado
    """
    import json
    from datetime import datetime

    from app.arkmeds_client.models import Chamado

    if df.empty:
        return {
            "corrective_building": [],
            "corrective_engineering": [],
            "preventive_building": [],
            "preventive_infra": [],
            "active_search": [],
            "open_orders": [],
            "closed_orders": [],
        }

    # Converter para objetos Chamado otimizadamente
    orders = []

    for _, row in df.iterrows():
        try:
            # Preparar dados do chamado
            chamado_data = {
                "id": row["id"],
                "data_criacao": row["data_criacao"],
                "chamados": row["chamados"] or [],
            }

            # Processar ordem_servico (pode estar como JSON string ou dict)
            os_data = row["ordem_servico"]
            if isinstance(os_data, str):
                try:
                    os_data = json.loads(os_data)
                except json.JSONDecodeError:
                    continue

            chamado_data["ordem_servico"] = os_data

            # Adicionar campos opcionais
            if pd.notna(row.get("data_fechamento")):
                chamado_data["data_fechamento"] = row["data_fechamento"]

            if pd.notna(row.get("responsavel_id")):
                chamado_data["responsavel_id"] = row["responsavel_id"]

            # Criar objeto Chamado
            order = Chamado.model_validate(chamado_data)
            orders.append(order)

        except Exception:
            # Pular registros inválidos silenciosamente
            continue

    # ========== FILTROS E CATEGORIZAÇÃO OTIMIZADOS ==========

    # Filtrar por data (usando datetime para comparação precisa)
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    date_filtered_orders = []
    for order in orders:
        try:
            if order.data_criacao:
                # Lidar com diferentes formatos de data
                if isinstance(order.data_criacao, str):
                    order_date = datetime.fromisoformat(order.data_criacao.replace("Z", "+00:00"))
                elif hasattr(order.data_criacao, "replace"):  # datetime object
                    order_date = order.data_criacao
                else:
                    continue

                # Aplicar filtro de data
                if start_datetime <= order_date <= end_datetime:
                    date_filtered_orders.append(order)
        except Exception:
            continue

    # Categorizar orders otimizadamente
    categorized = {
        "corrective_building": [],
        "corrective_engineering": [],
        "preventive_building": [],
        "preventive_infra": [],
        "active_search": [],
        "open_orders": [],
        "closed_orders": [],
    }

    for order in date_filtered_orders:
        try:
            # Extrair tipo e área do order
            if not order.ordem_servico:
                continue

            tipo_servico = order.ordem_servico.get("tipo_servico")
            estado = order.ordem_servico.get("estado")
            area = order.ordem_servico.get("area")

            # Categorizar por estado (aberto/fechado)
            if estado in [1, 2, 3, 4]:  # Estados abertos
                categorized["open_orders"].append(order)
            elif estado in [5, 6]:  # Estados fechados
                categorized["closed_orders"].append(order)

            # Categorizar por tipo e área
            if tipo_servico == TIPO_CORRETIVA:
                if area == AREA_PREDIAL:
                    categorized["corrective_building"].append(order)
                elif area == AREA_ENG_CLIN:
                    categorized["corrective_engineering"].append(order)

            elif tipo_servico == TIPO_PREVENTIVA:
                if area == AREA_PREDIAL:
                    categorized["preventive_building"].append(order)
                elif area == AREA_ENG_CLIN:
                    categorized["preventive_infra"].append(order)

            elif tipo_servico == TIPO_BUSCA_ATIVA:
                categorized["active_search"].append(order)

        except Exception:
            continue

    return categorized


async def fetch_service_orders(
    client: ArkmedsClient, start_date: date, end_date: date, **filters: Any
) -> ServiceOrderData:
    """Fetch all service orders data concurrently.

    This function makes parallel API calls to fetch different types of service orders
    to minimize total request time.

    Args:
        client: The Arkmeds API client instance
        start_date: Start date for the query (inclusive)
        end_date: End date for the query (inclusive)
        **filters: Additional filters to apply to all queries

    Returns:
        Dictionary containing categorized lists of service orders:
        - corrective_building: Corrective orders for building maintenance
        - corrective_engineering: Corrective orders for clinical engineering
        - preventive_building: Preventive orders for building maintenance
        - preventive_infra: Preventive orders for infrastructure
        - active_search: Active search orders
        - open_orders: Currently open corrective orders
        - closed_orders: All closed corrective orders
        - closed_in_period: Corrective orders closed within the date range

    Raises:
        DataFetchError: If there's an error fetching data from the API
        ValidationError: If input parameters are invalid
    """
    _validate_dates(start_date, end_date)

    try:
        sanitized_filters = dict(filters)
        extra_estado_ids = sanitized_filters.pop("estado_ids", None)

        # Prepare common parameters
        common_params = {
            "data_criacao__gte": start_date,
            "data_criacao__lte": end_date,
            **sanitized_filters,
        }
        if extra_estado_ids is not None:
            common_params["estado_ids"] = extra_estado_ids

        # Define all the queries to run in parallel
        queries = [
            # Corrective orders by area
            fetch_orders(client, TIPO_CORRETIVA, AREA_PREDIAL, **common_params),
            fetch_orders(client, TIPO_CORRETIVA, AREA_ENG_CLIN, **common_params),
            # Preventive orders by area
            fetch_orders(client, TIPO_PREVENTIVA, AREA_PREDIAL, **common_params),
            fetch_orders(client, TIPO_PREVENTIVA, AREA_ENG_CLIN, **common_params),
            # Active search orders
            fetch_orders(client, TIPO_BUSCA_ATIVA, **common_params),
            # Open and closed orders for backlog calculation
            fetch_orders(
                client,
                TIPO_CORRETIVA,
                estado_ids=[OSEstado.ABERTA.value],
                **sanitized_filters,  # Don't apply date filters for backlog
            ),
            fetch_orders(
                client,
                TIPO_CORRETIVA,
                estado_ids=[OSEstado.FECHADA.value],
                **sanitized_filters,  # Don't apply date filters for backlog
            ),
            # Orders closed in the period for SLA calculation
            fetch_orders(
                client,
                TIPO_CORRETIVA,
                estado_ids=[OSEstado.FECHADA.value],
                data_fechamento__gte=start_date,
                data_fechamento__lte=end_date,
                **sanitized_filters,
            ),
        ]

        # Execute all queries in parallel
        results = await asyncio.gather(*queries, return_exceptions=False)

        # Map results to named fields with type safety
        return {
            "corrective_building": cast(list[Chamado], results[0]),
            "corrective_engineering": cast(list[Chamado], results[1]),
            "preventive_building": cast(list[Chamado], results[2]),
            "preventive_infra": cast(list[Chamado], results[3]),
            "active_search": cast(list[Chamado], results[4]),
            "open_orders": cast(list[Chamado], results[5]),
            "closed_orders": cast(list[Chamado], results[6]),
            "closed_in_period": cast(list[Chamado], results[7]),
        }

    except (httpx.TimeoutException, ArkmedsAuthError) as exc:
        raise DataFetchError(f"Failed to fetch service orders data: {exc!s}") from exc
    except Exception as exc:
        raise OSMetricsError(f"Unexpected error while fetching service orders: {exc!s}") from exc


async def calculate_sla_metrics(closed_orders: list[Chamado]) -> float:
    """Calculate SLA compliance percentage based on closed orders.

    Args:
        closed_orders: List of closed service orders to analyze

    Returns:
        float: SLA compliance percentage (0-100), or 0 if no orders provided

    Raises:
        ValidationError: If orders list is not a valid sequence
    """
    # Validar dados usando helpers de data/validators.py
    from app.data.validators import validate_input_data

    validate_input_data(closed_orders, list, "closed_orders must be a list")

    if not closed_orders:
        return 0.0

    try:
        # Contar ordens finalizadas sem atraso usando as propriedades do modelo Chamado
        within_sla = sum(
            1
            for order in closed_orders
            if order.finalizado_sem_atraso  # Usar propriedade do modelo
        )

        return (within_sla / len(closed_orders)) * 100

    except (TypeError, AttributeError) as exc:
        raise ValidationError("Invalid order objects in closed_orders list") from exc
    except Exception as exc:
        raise OSMetricsError(f"Error calculating SLA metrics: {exc!s}") from exc


async def _cached_compute(
    start_date: date,
    end_date: date,
    frozen_filters: tuple[tuple[str, Any], ...],
    _client: ArkmedsClient,
) -> dict[str, Any]:
    """Cached computation of service order metrics.

    Returns a dict representation of OSMetrics for better pickle compatibility.

    This function is wrapped with Streamlit's cache decorator to avoid
    redundant computations. The cache is invalidated when:
    - The TTL (15 minutes) expires
    - The input parameters change
    - The function code changes

    Args:
        start_date: Start date for metrics calculation
        end_date: End date for metrics calculation
        frozen_filters: Immutable representation of filters
        _client: Arkmeds client (prefixed with _ to exclude from cache key)

    Returns:
        dict: Dictionary representation of OSMetrics
    """
    try:
        filters = dict(frozen_filters)
        metrics = await _async_compute_metrics(_client, start_date, end_date, filters)
        # Convert to dict for better pickle compatibility
        return {
            "corrective_building": metrics.corrective_building,
            "corrective_engineering": metrics.corrective_engineering,
            "preventive_building": metrics.preventive_building,
            "preventive_infra": metrics.preventive_infra,
            "active_search": metrics.active_search,
            "backlog": metrics.backlog,
            "sla_percentage": metrics.sla_percentage,
        }
    except Exception as exc:
        st.error(f"Erro ao calcular métricas: {exc!s}")
        raise


async def _async_compute_metrics(
    client: ArkmedsClient,
    start_date: date,
    end_date: date,
    filters: dict[str, Any],
) -> OSMetrics:
    """Compute all service order metrics asynchronously.

    This is the core function that orchestrates the data fetching and metric
    calculation pipeline.

    Args:
        client: The Arkmeds API client
        start_date: Start date for metrics
        end_date: End date for metrics
        filters: Additional filters to apply

    Returns:
        OSMetrics: Populated metrics object

    Raises:
        OSMetricsError: If there's an error computing metrics
    """
    try:
        # Fetch all required data using cache-enabled function
        data = await fetch_service_orders_with_cache(client, start_date, end_date, **filters)

        # Calculate backlog (open orders - closed orders)
        # Ensure we don't go below zero in case of data inconsistencies
        backlog = max(0, len(data["open_orders"]) - len(data["closed_orders"]))

        # Calculate SLA percentage with error handling
        try:
            sla_pct = await calculate_sla_metrics(data["closed_in_period"])
        except Exception as exc:
            st.warning(f"Could not calculate SLA metrics: {exc!s}")
            sla_pct = 0.0

        # Create and return the metrics object
        return OSMetrics(
            corrective_building=len(data["corrective_building"]),
            corrective_engineering=len(data["corrective_engineering"]),
            preventive_building=len(data["preventive_building"]),
            preventive_infra=len(data["preventive_infra"]),
            active_search=len(data["active_search"]),
            backlog=backlog,
            sla_percentage=round(sla_pct, 2),  # Round to 2 decimal places
        )

    except Exception as exc:
        raise OSMetricsError(f"Error computing service order metrics: {exc!s}") from exc


async def compute_metrics(
    client: ArkmedsClient,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    dt_ini: date | None = None,
    dt_fim: date | None = None,
    **filters: Any,
) -> OSMetrics:
    """Public interface to compute service order metrics.

    This is the main entry point that should be called from other modules.
    It provides a clean, typed interface and handles:
    - Input validation
    - Background thread execution
    - Caching
    - Error handling

    Example:
        ```python
        metrics = await compute_metrics(
            client,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            unidade_id=1
        )
        ```

    Args:
        client: The Arkmeds API client instance
        start_date: Start date for metrics (inclusive)
        end_date: End date for metrics (inclusive)
        **filters: Additional filters (e.g., unidade_id, setor_id)

    Returns:
        OSMetrics: Object containing all computed metrics

    Raises:
        OSMetricsError: If there's an error computing metrics
        ValidationError: If input parameters are invalid
    """
    try:
        # Garantir que as datas não sejam None, usar fallbacks
        if start_date is None:
            start_date = dt_ini
        if end_date is None:
            end_date = dt_fim

        # Se ainda são None, usar período padrão (último mês)
        if start_date is None:
            from datetime import date

            start_date = date.today().replace(day=1)  # Primeiro dia do mês
        if end_date is None:
            from datetime import date

            end_date = date.today()

        # Input validation
        _validate_dates(start_date, end_date)

        # Convert filters to a hashable type for caching
        frozen = tuple(sorted(filters.items()))

        metrics_dict = await _cached_compute(
            start_date,
            end_date,
            frozen,
            client,
        )

        # Convert dict back to OSMetrics object
        return OSMetrics(**metrics_dict)

    except ValidationError:
        raise  # Re-raise validation errors as-is
    except Exception as exc:
        raise OSMetricsError(f"Failed to compute service order metrics: {exc!s}") from exc
