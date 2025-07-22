from datetime import datetime

from app.arkmeds_client.models import Equipment, OS, User, TipoOS, EstadoOS, OSEstado


def test_os_validation():
    payload = {
        "id": 10,
        "tipo_ordem_servico": {"id": 1, "descricao": "Preventiva"},
        "estado": {"id": OSEstado.ABERTA.value, "descricao": "Aberta"},
        "responsavel": {
            "id": 3,
            "nome": "Joao",
            "email": "joao@example.com",
            "cargo": "Tec",
            "extra": 1,
        },
        "data_criacao": "01/07/25 - 08:00",
        "data_fechamento": "02/07/25 - 10:00",
        "ignored": True,
    }
    os_obj = OS.model_validate(payload)
    assert isinstance(os_obj.created_at, datetime)
    assert isinstance(os_obj.closed_at, datetime)
    assert os_obj.responsavel
    assert os_obj.responsavel.email == "joao@example.com"
    assert not hasattr(os_obj, "ignored")


def test_equipment_validation():
    payload = {
        "id": 5,
        "nome": "Monitor",
        "ativo": True,
        "data_aquisicao": "05/05/25 - 00:00",
        "foo": "bar",
    }
    equip = Equipment.model_validate(payload)
    assert isinstance(equip.data_aquisicao, datetime)
    assert not hasattr(equip, "foo")
