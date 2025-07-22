from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
import streamlit as st
from dateutil import parser

from .models import TokenData


class ArkmedsAuthError(Exception):
    pass


class ArkmedsAuth:
    def __init__(self, email: str, password: str, base_url: str, max_tries: int = 3) -> None:
        self.email = email
        self.password = password
        self.base_url = base_url.rstrip("/")
        self.max_tries = max_tries
        self._token: Optional[TokenData] = None
        self._client: Optional[httpx.AsyncClient] = None

    @classmethod
    def from_secrets(cls) -> "ArkmedsAuth":
        cfg = st.secrets.get("arkmeds", {})
        return cls(
            email=cfg.get("email", ""),
            password=cfg.get("password", ""),
            base_url=cfg.get("base_url", ""),
        )

    async def _get_client(self) -> httpx.AsyncClient:
        if not self._client:
            self._client = httpx.AsyncClient(base_url=self.base_url)
        return self._client

    async def login(self) -> TokenData:
        client = await self._get_client()
        for attempt in range(self.max_tries):
            try:
                resp = await client.post(
                    "/api/v3/auth/login/",
                    json={"email": self.email, "password": self.password},
                    timeout=10,
                )
                if resp.status_code == 401:
                    raise ArkmedsAuthError("Invalid credentials")
                resp.raise_for_status()
                data = resp.json()
                token = data.get("token") or data.get("access")
                exp_raw = data.get("exp") or data.get("expires_in") or data.get("expires")
                if token is None or exp_raw is None:
                    raise ArkmedsAuthError("Malformed login response")
                if isinstance(exp_raw, (int, float)):
                    exp = datetime.fromtimestamp(exp_raw, tz=timezone.utc)
                else:
                    exp = parser.isoparse(str(exp_raw))
                self._token = TokenData(token=token, exp=exp)
                st.session_state["arkmeds_token"] = token
                return self._token
            except httpx.RequestError as exc:
                if attempt == self.max_tries - 1:
                    raise ArkmedsAuthError("Connection error") from exc
                await asyncio.sleep(2 ** attempt)
        raise ArkmedsAuthError("Unable to authenticate")

    async def refresh(self) -> None:
        if not self._token:
            await self.login()
            return
        remaining = self._token.exp - datetime.now(timezone.utc)
        if remaining < timedelta(seconds=300):
            await self.login()

    async def get_token(self) -> str:
        if not self._token:
            await self.login()
        await self.refresh()
        assert self._token  # for type checkers
        return self._token.token
