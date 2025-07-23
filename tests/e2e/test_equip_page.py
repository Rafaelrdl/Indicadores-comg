import os
import sys
from datetime import datetime

import pandas as pd
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

with open(os.path.join(ROOT, "app", "ui", "equip.py"), encoding="utf-8") as f:
    src = f.read()
start = src.index("def _build_history_df")
end = src.index("@st.cache_data")
ns: dict[str, any] = {}
from collections import defaultdict
from datetime import date
from statistics import mean
import pandas as pd  # noqa: E402
from app.arkmeds_client.models import OS
ns.update(dict(defaultdict=defaultdict, mean=mean, date=date, pd=pd, OS=OS))
exec(src[start:end], ns)
_build_history_df = ns["_build_history_df"]

from app.arkmeds_client.models import OS, TipoOS, OSEstado, EstadoOS


def make_os(id: int, eq: int, created: datetime, closed: datetime) -> OS:
    payload = {
        "id": id,
        "tipo_ordem_servico": {"id": TipoOS(id=1, descricao="c").id, "descricao": "c"},
        "estado": {"id": OSEstado.FECHADA.value, "descricao": "f"},
        "data_criacao": created.strftime("%d/%m/%y - %H:%M"),
        "data_fechamento": closed.strftime("%d/%m/%y - %H:%M"),
        "equipamento_id": eq,
    }
    return OS.model_validate(payload)


@pytest.mark.asyncio
async def test_history_df_builds():
    os_list = [
        make_os(1, 1, datetime(2025, 1, 1, 10), datetime(2025, 1, 2, 10)),
        make_os(2, 1, datetime(2025, 2, 3, 9), datetime(2025, 2, 5, 9)),
        make_os(3, 1, datetime(2025, 3, 1, 8), datetime(2025, 3, 2, 8)),
    ]
    df = _build_history_df(os_list)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
