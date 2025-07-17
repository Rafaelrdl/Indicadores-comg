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
# Credenciais padrão podem ser definidas via variáveis de ambiente
EMAIL = os.getenv("ARKMEDS_EMAIL")
PASSWORD = os.getenv("ARKMEDS_PASSWORD")

# Token obtido após a autenticação; guardado em memória
_TOKEN: Optional[str] = None
# Timestamp de quando o token foi obtido
_TS = 0.0
# Tempo em segundos para expiração do token
TTL = 3600  # 1 hour


def set_credentials(email: str, password: str) -> None:
    """Configure credentials used to authenticate with Arkmeds."""
    global EMAIL, PASSWORD, _TOKEN, _TS
    EMAIL = email
    PASSWORD = password
    _TOKEN = None
    _TS = 0.0


def get_token(force: bool = False) -> str:
    """Return a valid token, refreshing if necessary."""
    global _TOKEN, _TS
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
    resp = requests.request(
        method, f"{BASE_URL}{endpoint}", headers=headers, timeout=15, **kwargs
    )
    if resp.status_code == 401:
        # Token expirado: tenta novamente forçando renovação
        headers["Authorization"] = f"Token {get_token(force=True)}"
        resp = requests.request(
            method, f"{BASE_URL}{endpoint}", headers=headers, timeout=15, **kwargs
        )
    # Dispara uma exceção caso a resposta indique erro HTTP
    resp.raise_for_status()
    return resp.json()


def get_assets(**params: Any) -> Any:
    """Retrieve asset list from the API."""
    return _request("GET", "/assets/", params=params)


def get_workorders(status: Optional[str] = None, **params: Any) -> Any:
    """Retrieve work orders, optionally filtering by status."""
    if status is not None:
        params["status"] = status
    return _request("GET", "/workorders/", params=params)


def get_tickets(status: Optional[str] = None, **params: Any) -> Any:
    """Retrieve tickets, optionally filtering by status."""
    if status is not None:
        params["status"] = status
    return _request("GET", "/tickets/", params=params)
