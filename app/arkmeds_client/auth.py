from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
import streamlit as st

from .models import TokenData


class ArkmedsAuthError(Exception):
    pass


class ArkmedsAuth:
    """Handle authentication against the Arkmeds API.

    The login endpoint can be configured via ``login_path`` or the
    ``ARKMEDS_LOGIN_PATH`` environment variable.
    """

    # Ordered list of possible login endpoints. The first one that works will
    # be cached for subsequent logins.
    LOGIN_ENDPOINT_CANDIDATES = [
        "/rest-auth/token-auth/",
        "/rest-auth/login/",
        "/api/v5/auth/login/",
        "/api/v3/auth/login",
        "/api/v3/login",
        "/api/auth/login",
    ]

    def __init__(
        self,
        email: str,
        password: str,
        base_url: str,
        token: str | None = None,
        max_tries: int = 3,
        login_path: str | None = None,
    ) -> None:
        if not base_url.startswith(("http://", "https://")):
            raise ValueError("base_url must start with 'http://' or 'https://'")
        self.email = email
        self.password = password
        self.base_url = base_url.rstrip("/")
        self.max_tries = max_tries
        if token:
            exp = datetime.now(timezone.utc) + timedelta(hours=1)
            self._token = TokenData(token=token, exp=exp)
            st.session_state["arkmeds_token"] = token
        else:
            self._token = None
        self._client: Optional[httpx.AsyncClient] = None
        self._login_url: Optional[str] = login_path or os.environ.get("ARKMEDS_LOGIN_PATH")

    @classmethod
    def from_secrets(cls) -> "ArkmedsAuth":
        cfg = st.secrets.get("arkmeds", {})
        return cls(
            email=cfg.get("email", ""),
            password=cfg.get("password", ""),
            base_url=cfg.get("base_url", ""),
            token=cfg.get("token"),
            login_path=cfg.get("login_path"),
        )

    async def _get_client(self) -> httpx.AsyncClient:
        if not self._client:
            self._client = httpx.AsyncClient(base_url=self.base_url)
        return self._client

    async def _discover_login_url(self) -> str:
        """Try to find a valid login endpoint by probing common paths."""
        if self._login_url:
            return self._login_url

        client = await self._get_client()

        async def check(path: str) -> str | None:
            for method in ("HEAD", "OPTIONS"):
                try:
                    resp = await client.request(method, path, timeout=0.2)
                    if resp.status_code in (200, 204, 405):
                        return path
                except httpx.RequestError:
                    pass
            return None

        tasks = [asyncio.create_task(check(p)) for p in self.LOGIN_ENDPOINT_CANDIDATES]

        done, pending = await asyncio.wait(
            tasks,
            timeout=0.3,
            return_when=asyncio.FIRST_COMPLETED,
        )
        for t in pending:
            t.cancel()

        for t in done:
            result = t.result()
            if result:
                self._login_url = result
                return result

        raise ArkmedsAuthError(
            "Login endpoint not found. Tried: " + ", ".join(self.LOGIN_ENDPOINT_CANDIDATES)
        )

    async def login(self) -> TokenData:
        """Authenticate against the Arkmeds API."""
        client = await self._get_client()

        if not self._login_url:
            await self._discover_login_url()

        endpoints = [self._login_url] if self._login_url else self.LOGIN_ENDPOINT_CANDIDATES
        last_404: Optional[httpx.Response] = None

        for endpoint in endpoints:
            for attempt in range(self.max_tries):
                try:
                    # Different endpoints may expect different payload formats
                    # Based on testing, /rest-auth/token-auth/ expects email/password
                    payload = {"email": self.email, "password": self.password}
                    
                    resp = await client.post(
                        endpoint,
                        json=payload,
                        timeout=10,
                    )

                    if resp.status_code == 401:
                        raise ArkmedsAuthError("Invalid credentials")
                    if resp.status_code == 400:
                        # Try to get more info from the response
                        try:
                            error_detail = resp.text
                            raise ArkmedsAuthError(f"Bad request to {endpoint}: {error_detail}")
                        except Exception:
                            raise ArkmedsAuthError(f"Bad request to {endpoint}")
                    if resp.status_code == 404:
                        last_404 = resp
                        break

                    resp.raise_for_status()
                    data = resp.json()
                    token = data.get("token") or data.get("access")
                    if token is None:
                        raise ArkmedsAuthError("Malformed login response")

                    exp = datetime.now(timezone.utc) + timedelta(hours=1)
                    self._token = TokenData(token=token, exp=exp)
                    st.session_state["arkmeds_token"] = token
                    self._login_url = endpoint
                    return self._token

                except httpx.RequestError as exc:
                    if attempt == self.max_tries - 1:
                        raise ArkmedsAuthError("Connection error") from exc
                    await asyncio.sleep(2**attempt)

            if self._token:
                break

        if last_404 is not None:
            raise ArkmedsAuthError(f"{last_404.status_code} {last_404.text}")
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


# Example:
# auth = ArkmedsAuth(base_url, email="e", password="p", login_path="/api/auth/token/login")
# await auth.login()
