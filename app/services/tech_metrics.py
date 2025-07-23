from __future__ import annotations

import asyncio
import os
from collections import defaultdict
from datetime import date
from typing import Any, Dict, Tuple

import httpx
import streamlit as st
from arkmeds_client.auth import ArkmedsAuthError
from arkmeds_client.client import ArkmedsClient
from arkmeds_client.models import OSEstado
from pydantic import BaseModel

SLA_HOURS = int(os.getenv("OS_SLA_HOURS", 72))


class TechMetricsError(Exception):
    """Raised when technician metrics computation fails."""


class TechKPI(BaseModel):
    tecnico_id: int
    nome: str
    abertas: int
    concluidas: int
    pendentes_total: int
    sla_pct: float
    avg_close_h: float


async def _async_compute(
    client: ArkmedsClient, *, dt_ini: date, dt_fim: date, filters: Dict[str, Any]
) -> list[TechKPI]:
    try:
        os_list = await client.list_os(
            data_criacao__lte=dt_fim,
            estado_ids=[OSEstado.ABERTA.value, OSEstado.FECHADA.value],
            **filters,
        )
    except (httpx.TimeoutException, ArkmedsAuthError) as exc:
        raise TechMetricsError("failed to fetch OS data") from exc

    valid = [o for o in os_list if o.estado.id != OSEstado.CANCELADA.value]

    by_tech: Dict[int, list] = defaultdict(list)
    for os_obj in valid:
        if os_obj.responsavel:
            by_tech[os_obj.responsavel.id].append(os_obj)

    results: list[TechKPI] = []
    for tech_id, items in by_tech.items():
        nome = items[0].responsavel.nome if items[0].responsavel else "?"
        abertas = len(
            [
                o
                for o in items
                if o.estado.id != OSEstado.FECHADA.value and o.created_at.date() >= dt_ini
            ]
        )
        concluidas_list = [
            o
            for o in items
            if o.estado.id == OSEstado.FECHADA.value
            and o.closed_at
            and dt_ini <= o.closed_at.date() <= dt_fim
        ]
        concluidas = len(concluidas_list)
        pendentes_total = len([o for o in items if o.estado.id != OSEstado.FECHADA.value])

        sla_ok = 0
        total_h = 0.0
        for o in concluidas_list:
            delta_h = (o.closed_at - o.created_at).total_seconds() / 3600
            total_h += delta_h
            if delta_h <= SLA_HOURS:
                sla_ok += 1
        sla_pct = round(sla_ok / concluidas * 100, 1) if concluidas else 0.0
        avg_close_h = round(total_h / concluidas, 2) if concluidas else 0.0

        results.append(
            TechKPI(
                tecnico_id=tech_id,
                nome=nome,
                abertas=abertas,
                concluidas=concluidas,
                pendentes_total=pendentes_total,
                sla_pct=sla_pct,
                avg_close_h=avg_close_h,
            )
        )

    results.sort(key=lambda k: k.pendentes_total, reverse=True)
    return results


def _freeze_filters(filters: Dict[str, Any]) -> Tuple[Tuple[str, Any], ...]:
    return tuple(sorted(filters.items()))


@st.cache_data(ttl=900)
def _cached_compute(
    dt_ini: date,
    dt_fim: date,
    frozen: Tuple[Tuple[str, Any], ...],
    _client: ArkmedsClient,
) -> list[TechKPI]:
    filters = dict(frozen)
    return asyncio.run(_async_compute(_client, dt_ini=dt_ini, dt_fim=dt_fim, filters=filters))


async def compute_metrics(
    client: ArkmedsClient, *, dt_ini: date, dt_fim: date, **filters: Any
) -> list[TechKPI]:
    frozen = _freeze_filters(filters)
    return await asyncio.to_thread(_cached_compute, dt_ini, dt_fim, frozen, client)