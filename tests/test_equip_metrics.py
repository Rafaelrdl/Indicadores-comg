from datetime import datetime, date

import pytest

from app.services.equip_metrics import compute_metrics, EquipMetrics
from app.arkmeds_client.models import Equipment, OS, OSEstado
from app.config.os_types import TIPO_CORRETIVA


class DummyClient:
    def __init__(self, equipments, os_list):
        self._equipments = equipments
        self._os = os_list

    async def list_equipment(self, **filters):
        return self._equipments

    async def list_os(self, **filters):
        assert filters.get("tipo_id") == TIPO_CORRETIVA
        return self._os


def make_equip(id, ativo=True):
    payload = {"id": id, "nome": f"E{id}", "ativo": ativo}
    return Equipment.model_validate(payload)


def make_os(id, eq_id, estado, created, closed=None):
    payload = {
        "id": id,
        "equipamento_id": eq_id,
        "tipo_ordem_servico": {"id": TIPO_CORRETIVA, "descricao": "c"},
        "estado": {"id": estado, "descricao": "e"},
        "data_criacao": created.strftime("%d/%m/%y - %H:%M"),
        "data_fechamento": closed.strftime("%d/%m/%y - %H:%M") if closed else None,
    }
    return OS.model_validate(payload)


@pytest.mark.asyncio
async def test_compute_equip_metrics():
    equipments = [make_equip(1), make_equip(2, False), make_equip(3)]

    os_list = [
        make_os(1, 1, OSEstado.ABERTA.value, datetime(2025, 1, 5)),
        make_os(
            2,
            1,
            OSEstado.FECHADA.value,
            datetime(2025, 1, 1),
            datetime(2025, 1, 3),
        ),
        make_os(
            3,
            2,
            OSEstado.FECHADA.value,
            datetime(2025, 1, 2),
            datetime(2025, 1, 5),
        ),
        make_os(
            4,
            1,
            OSEstado.FECHADA.value,
            datetime(2025, 1, 10),
            datetime(2025, 1, 12),
        ),
    ]

    client = DummyClient(equipments, os_list)
    metrics = await compute_metrics(client, dt_ini=date(2025, 1, 1), dt_fim=date(2025, 1, 31))

    assert isinstance(metrics, EquipMetrics)
    assert metrics.ativos == 2
    assert metrics.desativados == 1
    assert metrics.em_manutencao == 1
    assert metrics.mttr_h == 56.0
    assert metrics.mtbf_h == 216.0
