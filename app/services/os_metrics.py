from __future__ import annotations

import asyncio
import os
from datetime import date, timedelta
from typing import Any, Tuple

import httpx
import streamlit as st
from arkmeds_client.auth import ArkmedsAuthError
from arkmeds_client.client import ArkmedsClient
from arkmeds_client.models import OSEstado
from pydantic import BaseModel

from app.config.os_types import (
    AREA_ENG_CLIN,
    AREA_PREDIAL,
    TIPO_BUSCA_ATIVA,
    TIPO_CORRETIVA,
    TIPO_PREVENTIVA,
)

SLA_HOURS = int(os.getenv("OS_SLA_HOURS", 72))


class OSMetricsError(Exception):
    """Raised when metrics computation fails."""


class OSMetrics(BaseModel):
    corretivas_predial: int
    corretivas_engenharia: int
    preventivas_predial: int
    preventivas_infra: int
    busca_ativa: int
    backlog: int
    sla_pct: float


async def _async_compute(
    client: ArkmedsClient, *, dt_ini: date, dt_fim: date, filters: dict[str, Any]
) -> OSMetrics:
    async def fetch(tipo_id: int, area_id: int | None = None, **extra: Any):
        params: dict[str, Any] = {
            "tipo_id": tipo_id,
            "data_criacao__gte": dt_ini,
            "data_criacao__lte": dt_fim,
            **filters,
            **extra,
        }
        if area_id is not None:
            params["area_id"] = area_id
        return await client.list_os(**params)

    try:
        (
            corretivas_predial,
            corretivas_eng,
            preventivas_predial,
            preventivas_infra,
            busca,
            abertas,
            fechadas,
            fechadas_periodo,
        ) = await asyncio.gather(
            fetch(TIPO_CORRETIVA, AREA_PREDIAL),
            fetch(TIPO_CORRETIVA, AREA_ENG_CLIN),
            fetch(TIPO_PREVENTIVA, AREA_PREDIAL),
            fetch(TIPO_PREVENTIVA, AREA_ENG_CLIN),
            fetch(TIPO_BUSCA_ATIVA),
            fetch(TIPO_CORRETIVA, estado_ids=[OSEstado.ABERTA.value]),
            fetch(TIPO_CORRETIVA, estado_ids=[OSEstado.FECHADA.value]),
            fetch(
                TIPO_CORRETIVA,
                estado_ids=[OSEstado.FECHADA.value],
                data_fechamento__gte=dt_ini,
                data_fechamento__lte=dt_fim,
            ),
        )
    except (httpx.TimeoutException, ArkmedsAuthError) as exc:
        raise OSMetricsError("failed to fetch OS data") from exc

    backlog = len(abertas) - len(fechadas)

    within_sla = 0
    for os_obj in fechadas_periodo:
        if os_obj.closed_at and os_obj.closed_at - os_obj.created_at <= timedelta(hours=SLA_HOURS):
            within_sla += 1
    sla_pct = (within_sla / len(fechadas_periodo) * 100) if fechadas_periodo else 0.0

    return OSMetrics(
        corretivas_predial=len(corretivas_predial),
        corretivas_engenharia=len(corretivas_eng),
        preventivas_predial=len(preventivas_predial),
        preventivas_infra=len(preventivas_infra),
        busca_ativa=len(busca),
        backlog=backlog,
        sla_pct=round(sla_pct, 2),
    )


def _freeze_filters(filters: dict[str, Any]) -> Tuple[Tuple[str, Any], ...]:
    return tuple(sorted(filters.items()))


@st.cache_data(ttl=900)
def _cached_compute(
    dt_ini: date,
    dt_fim: date,
    frozen_filters: Tuple[Tuple[str, Any], ...],
    _client: ArkmedsClient,
) -> OSMetrics:
    filters = dict(frozen_filters)
    return asyncio.run(_async_compute(_client, dt_ini=dt_ini, dt_fim=dt_fim, filters=filters))


async def compute_metrics(
    client: ArkmedsClient, *, dt_ini: date, dt_fim: date, **filters: Any
) -> OSMetrics:
    frozen = _freeze_filters(filters)
    return await asyncio.to_thread(_cached_compute, dt_ini, dt_fim, frozen, client)