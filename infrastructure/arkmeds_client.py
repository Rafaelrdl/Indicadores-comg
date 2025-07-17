from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://api-os.arkmeds.com")
EMAIL = os.getenv("ARKMEDS_EMAIL")
PASSWORD = os.getenv("ARKMEDS_PASSWORD")

_TOKEN: Optional[str] = None
_TS = 0.0
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
    headers["Authorization"] = f"Token {get_token()}"
    resp = requests.request(
        method, f"{BASE_URL}{endpoint}", headers=headers, timeout=15, **kwargs
    )
    if resp.status_code == 401:
        headers["Authorization"] = f"Token {get_token(force=True)}"
        resp = requests.request(
            method, f"{BASE_URL}{endpoint}", headers=headers, timeout=15, **kwargs
        )
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
