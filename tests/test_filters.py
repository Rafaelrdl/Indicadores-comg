from datetime import date
import streamlit as st

from app.ui.filters import render_filters
from app.arkmeds_client.models import TipoOS, EstadoOS, User


class DummyClient:
    async def list_tipos(self):
        return [TipoOS.model_validate({"id": 1, "descricao": "Corretiva"})]

    async def list_estados(self):
        return [EstadoOS.model_validate({"id": 4, "descricao": "Fechada"})]

    async def list_users(self, perfil="responsavel_tecnico"):
        return [User.model_validate({"id": 2, "nome": "Joao", "email": "j"})]


def test_render_filters_persists(monkeypatch):
    class DummyState(dict):
        def clear(self):
            dict.clear(self)

    monkeypatch.setattr(st, "session_state", DummyState(), raising=False)
    st.session_state.clear()
    client = DummyClient()

    monkeypatch.setattr(st.sidebar, "date_input", lambda label, value=None: date(2025, 6, 1))
    monkeypatch.setattr(st.sidebar, "selectbox", lambda *a, **k: a[1][1])
    monkeypatch.setattr(st.sidebar, "multiselect", lambda *a, **k: [a[1][0]])

    clicked = {"apply": False}

    def fake_button(label):
        if label == "Aplicar" and not clicked["apply"]:
            clicked["apply"] = True
            return True
        return False

    monkeypatch.setattr(st.sidebar, "button", fake_button)

    render_filters(client)

    assert st.session_state["filters"]["dt_ini"] == date(2025, 6, 1)
    assert st.session_state["filters"]["tipo_id"] == 1
    assert st.session_state["filters"]["estado_ids"] == [4]
    assert st.session_state["filters"]["responsavel_id"] == 2
    assert st.session_state["filtros_version"] == 1
