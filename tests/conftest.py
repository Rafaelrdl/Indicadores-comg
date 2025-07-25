"""Configuração global para testes pytest."""

import sys
import pathlib

# Adicionar o diretório raiz do projeto ao PYTHONPATH
ROOT = pathlib.Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Configuração para Streamlit em ambiente de teste
import os
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
os.environ['STREAMLIT_SERVER_ENABLE_STATIC_SERVING'] = 'false'
os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

import pytest
from unittest.mock import MagicMock

@pytest.fixture(autouse=True)
def mock_streamlit():
    """Mock do Streamlit para testes que não precisam da UI."""
    import streamlit as st
    
    # Mock das funções principais do streamlit
    st.cache_data = lambda *args, **kwargs: lambda func: func
    st.error = MagicMock()
    st.warning = MagicMock()
    st.info = MagicMock()
    st.success = MagicMock()
    st.metric = MagicMock()
    st.dataframe = MagicMock()
    st.session_state = {}
    
    return st


@pytest.fixture
def sample_filters():
    """Fixture com filtros de exemplo para testes."""
    from datetime import date
    return {
        "dt_ini": date(2024, 1, 1),
        "dt_fim": date(2024, 12, 31),
        "tipo_id": None,
        "estado_ids": [],
        "responsavel_id": None,
    }


@pytest.fixture
def mock_arkmeds_client():
    """Mock do cliente ArkmedsClient."""
    from unittest.mock import AsyncMock
    
    client = MagicMock()
    client.list_equipment = AsyncMock(return_value=[])
    client.list_chamados = AsyncMock(return_value=[])
    client.list_os = AsyncMock(return_value=[])
    client.list_users = AsyncMock(return_value=[])
    
    return client
