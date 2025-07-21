import os, requests
from datetime import date
import streamlit as st

BASE_URL = os.getenv("ARKMEDS_BASE_URL", "").rstrip("/")
TOKEN = os.getenv("ARKMEDS_TOKEN", "")
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# IDs default conforme primeira especificação
ID_OS_CORRETIVA = int(os.getenv("ID_OS_CORRETIVA", 2))
ID_ESTADO_FECHADA = int(os.getenv("ID_ESTADO_FECHADA", 4))


@st.cache_data(ttl=86400)
def list_tipos():
    """Retorna [{id, label}] de tipos de OS."""
    url = f"{BASE_URL}/api/v3/tipo_ordem_servico/"
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return [{"id": t["id"], "label": t["descricao"]} for t in r.json()]


@st.cache_data(ttl=86400)
def list_estados():
    """Retorna [{id, label}] de estados de OS."""
    url = f"{BASE_URL}/api/v3/estado_ordem_servico/"
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return [{"id": e["id"], "label": e["descricao"]} for e in r.json()]


@st.cache_data(ttl=86400)
def list_responsaveis():
    """Retorna [{id, label}] de responsáveis técnicos."""
    url = f"{BASE_URL}/api/v5/usuarios/?perfil=responsavel_tecnico"
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return [{"id": u["id"], "label": u["nome"]} for u in r.json()["results"]]


@st.cache_data(ttl=3600)
def get_os_count(dt_ini, dt_fim, tipo_id=None, estado_ids=None, responsavel_id=None):
    """
    Retorna o count de OS segundo filtros.
    - Se algum filtro for None/ vazio, ele é ignorado.
    """
    params = {"data_criacao__gte": dt_ini, "data_criacao__lte": dt_fim, "page_size": 1}
    if tipo_id:
        params["id_tipo_ordem_servico"] = tipo_id
    if estado_ids:
        params["estado"] = ",".join(map(str, estado_ids))
    if responsavel_id:
        params["responsavel_tecnico"] = responsavel_id

    url = f"{BASE_URL}/api/v5/ordem_servico/"
    r = requests.get(url, headers=HEADERS, params=params, timeout=10)
    r.raise_for_status()
    return r.json()["count"]
