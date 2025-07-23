from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from statistics import mean
from typing import Any

import httpx
import streamlit as st
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


async def fetch_equipment_data(
    client: ArkmedsClient, 
    start_date: date, 
    end_date: date, 
    **filters: Any
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
        os_task = client.list_os(
            tipo_id=TIPO_CORRETIVA,
            data_criacao__gte=start_date,
            data_criacao__lte=end_date,
            **filters,
        )
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
    in_maintenance = {
        os_obj.equipment_id
        for os_obj in os_list
        if os_obj.equipment_id is not None 
        and os_obj.estado.id != OSEstado.FECHADA.value
    }

    # Calculate MTTR (Mean Time To Repair)
    closed_durations = [
        (os_obj.closed_at - os_obj.created_at).total_seconds()
        for os_obj in os_list
        if os_obj.closed_at
    ]
    mttr_h = mean(closed_durations) / 3600 if closed_durations else 0.0

    # Group by equipment and calculate MTBF
    by_equipment = defaultdict(list)
    for os_obj in os_list:
        if os_obj.equipment_id is not None and os_obj.closed_at:
            by_equipment[os_obj.equipment_id].append(os_obj)

    intervals = []
    for items in by_equipment.values():
        if len(items) < 2:
            continue
        items.sort(key=lambda o: o.created_at)
        for i in range(1, len(items)):
            intervals.append((items[i].created_at - items[i-1].created_at).total_seconds())
    
    mtbf_h = mean(intervals) / 3600 if intervals else 0.0

    return len(in_maintenance), mttr_h, mtbf_h


@st.cache_data(ttl=900)
def _cached_compute(
    start_date: date,
    end_date: date,
    frozen_filters: tuple[tuple[str, Any], ...],
    _client: ArkmedsClient,
) -> EquipmentMetrics:
    """Cached computation of equipment metrics.
    
    This function is wrapped with Streamlit's cache decorator to avoid
    redundant computations.
    """
    filters = dict(frozen_filters)
    return asyncio.run(_async_compute_metrics(_client, start_date, end_date, filters))


async def _async_compute_metrics(
    client: ArkmedsClient, 
    start_date: date, 
    end_date: date, 
    filters: dict[str, Any]
) -> EquipmentMetrics:
    """Compute all equipment metrics asynchronously.
    
    This is the main function that orchestrates the metrics computation.
    """
    equipment_list, os_list = await fetch_equipment_data(
        client, start_date, end_date, **filters
    )
    
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
    start_date: date, 
    end_date: date, 
    **filters: Any
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
    frozen = tuple(sorted(filters.items()))
    return await asyncio.to_thread(
        _cached_compute, 
        start_date, 
        end_date, 
        frozen, 
        client
    )