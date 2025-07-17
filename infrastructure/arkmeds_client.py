"""Simple client for the Arkmeds API used to fetch work orders and assets."""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

# Load variables defined in a local ``.env`` file, if present
load_dotenv()

# URL base da API
BASE_URL = os.getenv("BASE_URL")
# Prefixo usado por todos os endpoints de dados
API_PREFIX = os.getenv("ARKMEDS_API_PREFIX", "/api/v5").rstrip("/")
# Credenciais padrão podem ser definidas via variáveis de ambiente
EMAIL = os.getenv("ARKMEDS_EMAIL")
PASSWORD = os.getenv("ARKMEDS_PASSWORD")
# Token definido manualmente via variável de ambiente ou ``set_token``
_TOKEN_OVERRIDE: Optional[str] = os.getenv("ARKMEDS_TOKEN")

# Token obtido após a autenticação; guardado em memória
_TOKEN: Optional[str] = None
# Timestamp de quando o token foi obtido
_TS = 0.0
# Tempo em segundos para expiração do token
TTL = 3600  # 1 hour


def _url(path: str) -> str:
    """Concatena BASE_URL, prefixo e rota, evitando barras duplicadas."""
    if path.startswith("/"):
        path = path[1:]
    base = BASE_URL.rstrip("/")
    if base.endswith(API_PREFIX):
        return f"{base}/{path}"
    return f"{base}{API_PREFIX}/{path}"


def set_credentials(email: str, password: str) -> None:
    """Configure credentials used to authenticate with Arkmeds."""
    global EMAIL, PASSWORD, _TOKEN, _TS
    EMAIL = email
    PASSWORD = password
    _TOKEN = None
    _TS = 0.0


def set_token(token: str) -> None:
    """Configure a fixed authentication token."""
    global _TOKEN_OVERRIDE
    _TOKEN_OVERRIDE = token


def get_token(force: bool = False) -> str:
    """Return a valid token, refreshing if necessary."""
    global _TOKEN, _TS
    if _TOKEN_OVERRIDE:
        return _TOKEN_OVERRIDE
    if not force and _TOKEN and time.time() - _TS < TTL:
        return _TOKEN
    if not EMAIL or not PASSWORD:
        raise RuntimeError("Credenciais Arkmeds não configuradas")
    resp = requests.post(
        f"{BASE_URL}/rest-auth/token-auth/",
        json={"email": EMAIL, "password": PASSWORD},
        timeout=10,
    )
    resp.raise_for_status()
    _TOKEN = resp.json()["token"]
    _TS = time.time()
    return _TOKEN


def _request(method: str, endpoint: str, **kwargs: Any) -> Any:
    """Execute an authenticated request against the Arkmeds API."""
    headers: Dict[str, str] = kwargs.pop("headers", {})
    # Aplica o token atual no cabeçalho de autorização
    headers["Authorization"] = f"Token {get_token()}"
    url = _url(endpoint)
    resp = requests.request(method, url, headers=headers, timeout=15, **kwargs)
    if resp.status_code == 401:
        # Token expirado: tenta novamente forçando renovação
        headers["Authorization"] = f"Token {get_token(force=True)}"
        resp = requests.request(method, url, headers=headers, timeout=15, **kwargs)
    # Dispara uma exceção caso a resposta indique erro HTTP
    resp.raise_for_status()
    return resp.json()


def get_assets(**params: Any) -> Any:
    """Retrieve asset list from the API."""
    return _request("GET", "assets/", params=params)


def get_ordens_servico(page: int | None = None, page_size: int = 30) -> Any:
    """Retrieve ordens de serviço from the API."""
    params = (
        {"page": page, "page_size": page_size} if page else {"page_size": page_size}
    )
    return _request("GET", "ordem_servico/", params=params)


# Mantém alias para retrocompatibilidade
get_workorders = get_ordens_servico


def get_tickets(status: Optional[str] = None, **params: Any) -> Any:
    """Retrieve tickets, optionally filtering by status."""
    if status is not None:
        params["status"] = status
    return _request("GET", "tickets/", params=params)
