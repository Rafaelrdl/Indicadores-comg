from datetime import datetime, date

import pytest

from app.services.os_metrics import compute_metrics
from app.services.os_metrics import OSMetrics
from app.arkmeds_client.models import OS, OSEstado


class DummyClient:
    def __init__(self, mapping):
        self.mapping = mapping

    async def list_os(self, **filters):
        key = filters.get("label")
        return self.mapping.get(key, [])


def make_os(id, tipo, estado, created, closed=None):
    payload = {
        "id": id,
        "tipo_ordem_servico": {"id": tipo, "descricao": "t"},
        "estado": {"id": estado, "descricao": "e"},
        "data_criacao": created.strftime("%d/%m/%y - %H:%M"),
        "data_fechamento": closed.strftime("%d/%m/%y - %H:%M") if closed else None,
    }
    return OS.model_validate(payload)


@pytest.mark.asyncio
async def test_compute_metrics():
    dt_ini = date(2025, 1, 1)
    dt_fim = date(2025, 1, 31)

    data = {
        "cor_predial": [make_os(1, 2, 1, datetime(2025, 1, 5))],
        "cor_eng": [make_os(2, 2, 1, datetime(2025, 1, 6)) for _ in range(2)],
        "prev_predial": [make_os(3, 1, 1, datetime(2025, 1, 7)) for _ in range(3)],
        "prev_infra": [make_os(4, 1, 1, datetime(2025, 1, 8))],
        "busca": [make_os(5, 6, 1, datetime(2025, 1, 9)) for _ in range(4)],
        "abertas": [make_os(6, 2, OSEstado.ABERTA.value, datetime(2025, 1, 10)) for _ in range(6)],
        "fechadas": [make_os(7, 2, OSEstado.FECHADA.value, datetime(2025, 1, 11)) for _ in range(2)],
        "fechadas_periodo": [
            make_os(
                8,
                2,
                OSEstado.FECHADA.value,
                datetime(2025, 1, 12),
                datetime(2025, 1, 13),
            ),
            make_os(
                9,
                2,
                OSEstado.FECHADA.value,
                datetime(2025, 1, 14),
                datetime(2025, 2, 20),
            ),
        ],
    }

    client = DummyClient(data)

    async def fake_list_os(**filters):
        if filters.get("estado_ids") == [OSEstado.ABERTA.value]:
            return data["abertas"]
        if filters.get("data_fechamento__gte"):
            return data["fechadas_periodo"]
        if filters.get("estado_ids") == [OSEstado.FECHADA.value]:
            return data["fechadas"]
        if filters.get("tipo_id") == 2 and filters.get("area_id") == 10:
            return data["cor_predial"]
        if filters.get("tipo_id") == 2 and filters.get("area_id") == 11:
            return data["cor_eng"]
        if filters.get("tipo_id") == 1 and filters.get("area_id") == 10:
            return data["prev_predial"]
        if filters.get("tipo_id") == 1 and filters.get("area_id") == 11:
            return data["prev_infra"]
        if filters.get("tipo_id") == 6:
            return data["busca"]
        return []

    client.list_os = fake_list_os  # type: ignore[assignment]

    metrics = await compute_metrics(client, dt_ini=dt_ini, dt_fim=dt_fim)

    assert isinstance(metrics, OSMetrics)
    assert metrics.corretivas_predial == 1
    assert metrics.corretivas_engenharia == 2
    assert metrics.preventivas_predial == 3
    assert metrics.preventivas_infra == 1
    assert metrics.busca_ativa == 4
    assert metrics.backlog == 4
    assert metrics.sla_pct == 50.0
