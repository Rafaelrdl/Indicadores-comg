from datetime import datetime, date

import pytest

from app.services.tech_metrics import compute_metrics, TechKPI
from app.arkmeds_client.models import OS, OSEstado, User


class DummyClient:
    def __init__(self, os_list):
        self._os = os_list

    async def list_os(self, **filters):  # noqa: D401 - simple forward
        return self._os


def make_os(id, user, estado, created, closed=None):
    payload = {
        "id": id,
        "tipo_ordem_servico": {"id": 1, "descricao": "P"},
        "estado": {"id": estado, "descricao": "e"},
        "responsavel": {"id": user.id, "nome": user.nome, "email": "x"},
        "data_criacao": created.strftime("%d/%m/%y - %H:%M"),
        "data_fechamento": closed.strftime("%d/%m/%y - %H:%M") if closed else None,
    }
    return OS.model_validate(payload)


def make_user(id, nome):
    return User.model_validate({"id": id, "nome": nome, "email": "x"})


@pytest.mark.asyncio
async def test_compute_tech_metrics():
    dt_ini = date(2025, 1, 1)
    dt_fim = date(2025, 1, 31)

    u1 = make_user(1, "Tec1")
    u2 = make_user(2, "Tec2")

    os_list = [
        make_os(1, u1, OSEstado.ABERTA.value, datetime(2025, 1, 5)),
        make_os(2, u1, OSEstado.FECHADA.value, datetime(2025, 1, 2), datetime(2025, 1, 3)),
        make_os(3, u1, OSEstado.FECHADA.value, datetime(2024, 12, 31), datetime(2025, 1, 5)),
        make_os(4, u1, OSEstado.ABERTA.value, datetime(2024, 12, 10)),
        make_os(5, u1, OSEstado.CANCELADA.value, datetime(2025, 1, 10)),
        make_os(6, u2, OSEstado.ABERTA.value, datetime(2025, 1, 7)),
        make_os(7, u2, OSEstado.FECHADA.value, datetime(2025, 1, 8), datetime(2025, 1, 9)),
    ]

    client = DummyClient(os_list)
    metrics = await compute_metrics(client, dt_ini=dt_ini, dt_fim=dt_fim)

    assert isinstance(metrics, list)
    assert metrics[0].tecnico_id == 1
    assert metrics[0].abertas == 1
    assert metrics[0].concluidas == 2
    assert metrics[0].pendentes_total == 2
    assert metrics[0].sla_pct == 50.0
    assert metrics[0].avg_close_h == 72.0

    assert metrics[1].tecnico_id == 2
    assert metrics[1].abertas == 1
    assert metrics[1].concluidas == 1
    assert metrics[1].pendentes_total == 1
    assert metrics[1].sla_pct == 100.0
    assert metrics[1].avg_close_h == 24.0
