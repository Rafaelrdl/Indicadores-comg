from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import date
from statistics import mean
from typing import Any, Dict, Tuple

import httpx
import streamlit as st
from pydantic import BaseModel

from app.arkmeds_client.auth import ArkmedsAuthError
from app.arkmeds_client.client import ArkmedsClient
from app.arkmeds_client.models import OSEstado
from app.config.os_types import TIPO_CORRETIVA


class EquipMetricsError(Exception):
    """Raised when equipment metrics computation fails."""


class EquipMetrics(BaseModel):
    ativos: int
    desativados: int
    em_manutencao: int
    mttr_h: float
    mtbf_h: float


async def _async_compute(
    client: ArkmedsClient, *, dt_ini: date, dt_fim: date, filters: Dict[str, Any]
) -> EquipMetrics:
    try:
        equip_task = client.list_equipment()
        os_task = client.list_os(
            tipo_id=TIPO_CORRETIVA,
            data_criacao__gte=dt_ini,
            data_criacao__lte=dt_fim,
            **filters,
        )
        equip_list, os_corr = await asyncio.gather(equip_task, os_task)
    except (httpx.TimeoutException, ArkmedsAuthError) as exc:
        raise EquipMetricsError("failed to fetch equipment data") from exc

    ativos = sum(1 for eq in equip_list if getattr(eq, "ativo", True))
    desativados = len(equip_list) - ativos

    manutencao_ids = {
        os_obj.equipment_id
        for os_obj in os_corr
        if os_obj.equipment_id is not None and os_obj.estado.id != OSEstado.FECHADA.value
    }
    em_manutencao = len(manutencao_ids)

    closed_durations = [
        (os_obj.closed_at - os_obj.created_at).total_seconds()
        for os_obj in os_corr
        if os_obj.closed_at
    ]
    mttr_h = mean(closed_durations) / 3600 if closed_durations else 0.0

    by_eq: Dict[int, list] = defaultdict(list)
    for os_obj in os_corr:
        if os_obj.equipment_id is not None and os_obj.closed_at:
            by_eq[os_obj.equipment_id].append(os_obj)

    intervals = []
    for items in by_eq.values():
        if len(items) < 2:
            continue
        items.sort(key=lambda o: o.created_at)
        for i in range(1, len(items)):
            intervals.append((items[i].created_at - items[i - 1].created_at).total_seconds())
    mtbf_h = mean(intervals) / 3600 if intervals else 0.0

    return EquipMetrics(
        ativos=ativos,
        desativados=desativados,
        em_manutencao=em_manutencao,
        mttr_h=round(mttr_h, 2),
        mtbf_h=round(mtbf_h, 2),
    )


def _freeze_filters(filters: Dict[str, Any]) -> Tuple[Tuple[str, Any], ...]:
    return tuple(sorted(filters.items()))


@st.cache_data(ttl=900)
def _cached_compute(
    dt_ini: date,
    dt_fim: date,
    frozen_filters: Tuple[Tuple[str, Any], ...],
    _client: ArkmedsClient,
) -> EquipMetrics:
    filters = dict(frozen_filters)
    return asyncio.run(_async_compute(_client, dt_ini=dt_ini, dt_fim=dt_fim, filters=filters))


async def compute_metrics(
    client: ArkmedsClient, *, dt_ini: date, dt_fim: date, **filters: Any
) -> EquipMetrics:
    frozen = _freeze_filters(filters)
    return await asyncio.to_thread(_cached_compute, dt_ini, dt_fim, frozen, client)
