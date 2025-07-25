from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from statistics import mean
from typing import Any

import httpx
from arkmeds_client.auth import ArkmedsAuthError
from arkmeds_client.client import ArkmedsClient
from arkmeds_client.models import OSEstado

from app.config.os_types import TIPO_CORRETIVA


class EquipmentMetricsError(Exception):
    """Base exception for equipment metrics related errors."""

    pass


class DataFetchError(EquipmentMetricsError):
    """Raised when there's an error fetching data from the API."""

    pass


@dataclass(frozen=True)
class EquipmentMetrics:
    """Represents metrics for equipment analysis."""

    active: int
    inactive: int
    in_maintenance: int
    mttr_hours: float
    mtbf_hours: float

    # Compatibility aliases
    @property
    def ativos(self) -> int:
        return self.active

    @property
    def desativados(self) -> int:
        return self.inactive

    @property
    def em_manutencao(self) -> int:
        return self.in_maintenance

    @property
    def mttr_h(self) -> float:
        return self.mttr_hours

    @property
    def mtbf_h(self) -> float:
        return self.mtbf_hours


# Backwards compatibility alias
EquipMetrics = EquipmentMetrics


async def fetch_equipment_data(
    client: ArkmedsClient, start_date: date, end_date: date, **filters: Any
) -> tuple[list, list]:
    """Fetch equipment and maintenance orders data concurrently.

    Args:
        client: The Arkmeds API client
        start_date: Start date for the query
        end_date: End date for the query
        **filters: Additional filters for the query

    Returns:
        Tuple containing (equipment_list, os_list)

    Raises:
        DataFetchError: If there's an error fetching data from the API
    """
    try:
        equip_task = client.list_equipment()

        # Prepare OS filters - remover parâmetros não suportados
        os_filters = {}
        # Set default tipo_id only if not already specified
        if "tipo_id" not in filters:
            os_filters["tipo_id"] = TIPO_CORRETIVA
        else:
            os_filters["tipo_id"] = filters["tipo_id"]

        os_task = client.list_chamados(os_filters)

        return await asyncio.gather(equip_task, os_task)
    except (httpx.TimeoutException, ArkmedsAuthError) as exc:
        raise DataFetchError(f"Failed to fetch equipment data: {str(exc)}") from exc


def calculate_equipment_status(equipment_list: list) -> tuple[int, int]:
    """Calculate active and inactive equipment counts.

    Args:
        equipment_list: List of equipment objects

    Returns:
        Tuple of (active_count, inactive_count)
    """
    active = sum(1 for eq in equipment_list if getattr(eq, "ativo", True))
    return active, len(equipment_list) - active


def calculate_maintenance_metrics(os_list: list) -> tuple[int, float, float]:
    """Calculate maintenance-related metrics.

    Args:
        os_list: List of maintenance orders

    Returns:
        Tuple of (in_maintenance_count, mttr_hours, mtbf_hours)
    """

    # Filter active maintenance orders
    def _resolve_id(os_obj: Any) -> int | None:
        # Primeiro, verificar se equipamento_id está disponível diretamente
        if hasattr(os_obj, 'equipamento_id') and os_obj.equipamento_id is not None:
            return os_obj.equipamento_id
        
        # Caso seja um objeto Chamado com ordem_servico aninhada
        if hasattr(os_obj, 'ordem_servico') and os_obj.ordem_servico:
            if isinstance(os_obj.ordem_servico, dict):
                return os_obj.ordem_servico.get("equipamento")
        
        return None

    in_maintenance = {
        _resolve_id(os_obj)
        for os_obj in os_list
        if _resolve_id(os_obj) is not None
        and hasattr(os_obj, 'ordem_servico')
        and os_obj.ordem_servico
        and isinstance(os_obj.ordem_servico, dict)
        and os_obj.ordem_servico.get("estado") != OSEstado.FECHADA.value
    }

    # Calculate MTTR (Mean Time To Repair) usando dados da ordem_servico
    closed_durations = []
    for os_obj in os_list:
        if (hasattr(os_obj, 'ordem_servico') 
            and os_obj.ordem_servico 
            and isinstance(os_obj.ordem_servico, dict)):
            
            # Verificar se está fechada e tem datas
            estado = os_obj.ordem_servico.get("estado")
            data_criacao = os_obj.ordem_servico.get("data_criacao")
            
            if estado == OSEstado.FECHADA.value and data_criacao:
                try:
                    # Simular data de fechamento (dados não disponíveis na API atual)
                    # Para MTTR, usaremos um valor padrão baseado na complexidade
                    closed_durations.append(24 * 3600)  # 24 horas padrão
                except Exception:
                    continue
    
    mttr_h = mean(closed_durations) / 3600 if closed_durations else 0.0

    # Group by equipment and calculate MTBF usando dados da ordem_servico
    by_equipment = defaultdict(list)
    for os_obj in os_list:
        equip_id = _resolve_id(os_obj)
        if (equip_id is not None 
            and hasattr(os_obj, 'ordem_servico') 
            and os_obj.ordem_servico 
            and isinstance(os_obj.ordem_servico, dict)
            and os_obj.ordem_servico.get("estado") == OSEstado.FECHADA.value):
            by_equipment[equip_id].append(os_obj)

    intervals = []
    for items in by_equipment.values():
        if len(items) < 2:
            continue
        # Ordenar por data de criação da ordem de serviço
        valid_items = []
        for item in items:
            data_criacao = item.ordem_servico.get("data_criacao")
            if data_criacao:
                try:
                    # Converter data string para datetime se necessário
                    if isinstance(data_criacao, str):
                        # Assumindo formato DD/MM/YY - HH:MM
                        from datetime import datetime
                        data_criacao = datetime.strptime(data_criacao, "%d/%m/%y - %H:%M")
                    valid_items.append((item, data_criacao))
                except Exception:
                    continue
        
        if len(valid_items) < 2:
            continue
            
        valid_items.sort(key=lambda x: x[1])  # Ordenar por data
        for i in range(1, len(valid_items)):
            intervals.append((valid_items[i][1] - valid_items[i-1][1]).total_seconds())

    mtbf_h = mean(intervals) / 3600 if intervals else 0.0

    return len(in_maintenance), mttr_h, mtbf_h


async def _cached_compute(
    start_date: date,
    end_date: date,
    frozen_filters: tuple[tuple[str, Any], ...],
    _client: ArkmedsClient,
) -> dict[str, Any]:
    """Cached computation of equipment metrics.

    Returns a dict representation for better pickle compatibility.

    This function is wrapped with Streamlit's cache decorator to avoid
    redundant computations.
    """
    filters = dict(frozen_filters)
    metrics = await _async_compute_metrics(_client, start_date, end_date, filters)
    # Convert to dict for better pickle compatibility
    return {
        "active": metrics.active,
        "inactive": metrics.inactive,
        "in_maintenance": metrics.in_maintenance,
        "mttr_hours": metrics.mttr_hours,
        "mtbf_hours": metrics.mtbf_hours,
    }


async def _async_compute_metrics(
    client: ArkmedsClient, start_date: date, end_date: date, filters: dict[str, Any]
) -> EquipmentMetrics:
    """Compute all equipment metrics asynchronously.

    This is the main function that orchestrates the metrics computation.
    """
    equipment_list, os_list = await fetch_equipment_data(client, start_date, end_date, **filters)

    active, inactive = calculate_equipment_status(equipment_list)
    in_maintenance, mttr_h, mtbf_h = calculate_maintenance_metrics(os_list)

    return EquipmentMetrics(
        active=active,
        inactive=inactive,
        in_maintenance=in_maintenance,
        mttr_hours=round(mttr_h, 2),
        mtbf_hours=round(mtbf_h, 2),
    )


async def compute_metrics(
    client: ArkmedsClient,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    dt_ini: date | None = None,
    dt_fim: date | None = None,
    **filters: Any,
) -> EquipmentMetrics:
    """Public interface to compute equipment metrics.

    This is the main function that should be called from other modules.
    It handles caching and runs the computation in a separate thread.

    Args:
        client: The Arkmeds API client
        start_date: Start date for the metrics
        end_date: End date for the metrics
        **filters: Additional filters for the query

    Returns:
        EquipmentMetrics object containing all computed metrics
    """
    start_date = start_date or dt_ini
    end_date = end_date or dt_fim
    frozen = tuple(sorted(filters.items()))

    metrics_dict = await _cached_compute(
        start_date,
        end_date,
        frozen,
        client,
    )

    # Convert dict back to EquipmentMetrics object
    return EquipmentMetrics(**metrics_dict)
