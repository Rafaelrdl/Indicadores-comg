from __future__ import annotations

import asyncio
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import httpx
import streamlit as st
from arkmeds_client.auth import ArkmedsAuthError
from arkmeds_client.client import ArkmedsClient
from arkmeds_client.models import OSEstado

SLA_HOURS = int(os.getenv("OS_SLA_HOURS", 72))


class TechMetricsError(Exception):
    """Base exception for technician metrics related errors."""
    pass


class DataFetchError(TechMetricsError):
    """Raised when there's an error fetching data from the API."""
    pass


@dataclass(frozen=True)
class TechnicianKPI:
    """Represents key performance indicators for a technician."""
    technician_id: int
    name: str
    open_orders: int
    completed_orders: int
    total_pending: int
    sla_percentage: float
    average_close_hours: float


async def fetch_technician_orders(
    client: ArkmedsClient,
    start_date: date,
    end_date: date,
    **filters: Any
) -> list[Any]:
    """Fetch service orders data for technicians.
    
    Args:
        client: The Arkmeds API client
        start_date: Start date for the query
        end_date: End date for the query
        **filters: Additional filters for the query
        
    Returns:
        List of service orders
        
    Raises:
        DataFetchError: If there's an error fetching data from the API
    """
    try:
        return await client.list_os(
            data_criacao__lte=end_date,
            estado_ids=[OSEstado.ABERTA.value, OSEstado.FECHADA.value],
            **filters,
        )
    except (httpx.TimeoutException, ArkmedsAuthError) as exc:
        raise DataFetchError(f"Failed to fetch technician data: {str(exc)}") from exc


def group_orders_by_technician(orders: list[Any]) -> dict[int, list[Any]]:
    """Group service orders by technician.
    
    Args:
        orders: List of service orders
        
    Returns:
        Dictionary mapping technician IDs to their service orders
    """
    by_technician: dict[int, list[Any]] = defaultdict(list)
    for order in orders:
        if order.estado.id != OSEstado.CANCELADA.value and order.responsavel:
            by_technician[order.responsavel.id].append(order)
    return by_technician


def calculate_technician_kpis(
    technician_id: int,
    technician_name: str,
    orders: list[Any],
    start_date: date,
    end_date: date
) -> TechnicianKPI:
    """Calculate KPIs for a single technician.
    
    Args:
        technician_id: ID of the technician
        technician_name: Name of the technician
        orders: List of service orders for the technician
        start_date: Start date for the metrics period
        end_date: End date for the metrics period
        
    Returns:
        TechnicianKPI object with calculated metrics
    """
    # Filter relevant orders
    open_orders = [
        o for o in orders 
        if o.estado.id != OSEstado.FECHADA.value 
        and o.created_at.date() >= start_date
    ]
    
    completed_orders_list = [
        o for o in orders
        if o.estado.id == OSEstado.FECHADA.value
        and o.closed_at
        and start_date <= o.closed_at.date() <= end_date
    ]
    
    total_pending = len([o for o in orders if o.estado.id != OSEstado.FECHADA.value])
    
    # Calculate SLA metrics
    sla_ok = 0
    total_hours = 0.0
    
    for order in completed_orders_list:
        if not order.closed_at:
            continue
            
        duration_hours = (order.closed_at - order.created_at).total_seconds() / 3600
        total_hours += duration_hours
        
        if duration_hours <= SLA_HOURS:
            sla_ok += 1
    
    # Calculate final metrics
    completed_count = len(completed_orders_list)
    sla_percentage = round(sla_ok / completed_count * 100, 1) if completed_count > 0 else 0.0
    avg_close_hours = round(total_hours / completed_count, 2) if completed_count > 0 else 0.0
    
    return TechnicianKPI(
        technician_id=technician_id,
        name=technician_name,
        open_orders=len(open_orders),
        completed_orders=completed_count,
        total_pending=total_pending,
        sla_percentage=sla_percentage,
        average_close_hours=avg_close_hours,
    )


@st.cache_data(ttl=900)
def _cached_compute(
    start_date: date,
    end_date: date,
    frozen_filters: tuple[tuple[str, Any], ...],
    _client: ArkmedsClient,
) -> list[TechnicianKPI]:
    """Cached computation of technician metrics.
    
    This function is wrapped with Streamlit's cache decorator to avoid
    redundant computations.
    """
    filters = dict(frozen_filters)
    return asyncio.run(_async_compute_metrics(_client, start_date, end_date, filters))


async def _async_compute_metrics(
    client: ArkmedsClient,
    start_date: date,
    end_date: date,
    filters: dict[str, Any],
) -> list[TechnicianKPI]:
    """Compute all technician metrics asynchronously."""
    # Fetch service orders data
    orders = await fetch_technician_orders(client, start_date, end_date, **filters)
    
    # Group orders by technician
    by_technician = group_orders_by_technician(orders)
    
    # Calculate KPIs for each technician
    results = []
    for tech_id, tech_orders in by_technician.items():
        if not tech_orders or not tech_orders[0].responsavel:
            continue
            
        tech_name = tech_orders[0].responsavel.nome
        kpi = calculate_technician_kpis(
            tech_id, tech_name, tech_orders, start_date, end_date
        )
        results.append(kpi)
    
    # Sort by total pending orders (descending)
    results.sort(key=lambda x: x.total_pending, reverse=True)
    return results


async def compute_metrics(
    client: ArkmedsClient,
    *,
    start_date: date,
    end_date: date,
    **filters: Any
) -> list[TechnicianKPI]:
    """Public interface to compute technician metrics.
    
    This is the main function that should be called from other modules.
    It handles caching and runs the computation in a separate thread.
    
    Args:
        client: The Arkmeds API client
        start_date: Start date for the metrics
        end_date: End date for the metrics
        **filters: Additional filters for the query
        
    Returns:
        List of TechnicianKPI objects containing metrics for each technician
    """
    frozen = tuple(sorted(filters.items()))
    return await asyncio.to_thread(
        _cached_compute,
        start_date,
        end_date,
        frozen,
        client
    )