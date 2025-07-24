from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import httpx
import streamlit as st

from .auth import ArkmedsAuth, ArkmedsAuthError
from .models import (
    OS,
    Equipment,
    EstadoOS,
    PaginatedResponse,
    TipoOS,
    User,
)


class ArkmedsClient:
    @classmethod
    def from_session(cls) -> "ArkmedsClient":
        client = st.session_state.get("_arkmeds_client")
        if isinstance(client, cls):
            return client
        auth = ArkmedsAuth.from_secrets()
        client = cls(auth)
        st.session_state["_arkmeds_client"] = client
        return client

    def __init__(
        self,
        auth: ArkmedsAuth,
        *,
        timeout: float = 5.0,
        max_retries: int = 3,
    ) -> None:
        self.auth = auth
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if not self._client:
            token = await self.auth.get_token()
            headers = {"Authorization": f"JWT {token}"}
            self._client = httpx.AsyncClient(
                base_url=self.auth.base_url, 
                timeout=httpx.Timeout(self.timeout), 
                headers=headers,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        return self._client

    async def _request(
        self, method: str, url: str, *, params: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        client = await self._get_client()

        for attempt in range(self.max_retries):
            try:
                resp = await client.request(method, url, params=params)

                if resp.status_code == 401 and attempt == 0:
                    await self.auth.login()
                    client.headers["Authorization"] = f"JWT {await self.auth.get_token()}"
                    continue

                if resp.status_code == 403:
                    if attempt == 0:
                        await self.auth.login()
                        client.headers["Authorization"] = f"JWT {await self.auth.get_token()}"
                        continue
                    raise ArkmedsAuthError(f"{resp.status_code} {resp.text}")

                if resp.status_code >= 500 or resp.status_code == 429:
                    if attempt == self.max_retries - 1:
                        resp.raise_for_status()
                    await asyncio.sleep(2**attempt)
                    continue

                resp.raise_for_status()
                return resp
            except httpx.RequestError:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2**attempt)
        raise httpx.HTTPError("Max retries exceeded")

    async def _get_all_pages(self, endpoint: str, params: Dict[str, Any]) -> List[dict]:
        params = params.copy()
        params.setdefault("page", 1)
        params.setdefault("page_size", 100)

        url = endpoint
        results: List[dict] = []
        try:
            while url:
                resp = await self._request("GET", url, params=params if url == endpoint else None)
                data = PaginatedResponse.model_validate(resp.json())
                results.extend(data.results)
                url = data.next
                params = None
        except Exception:
            # Ensure client is closed on error
            await self.close()
            raise
        return results

    async def close(self) -> None:
        """Close the HTTP client connection."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def list_os(self, **filters: Any) -> List[OS]:
        data = await self._get_all_pages("/api/v3/ordem_servico/", filters)
        return [OS.model_validate(item) for item in data]

    async def list_equipment(self, **filters: Any) -> List[Equipment]:
        data = await self._get_all_pages("/api/v5/company/equipaments/", filters)
        return [Equipment.model_validate(item) for item in data]

    async def list_users(self, **filters: Any) -> List[User]:
        try:
            data = await self._get_all_pages("/api/v3/users/", filters)
            return [User.model_validate(item) for item in data]
        except (httpx.HTTPStatusError, httpx.RequestError, ConnectionError, RuntimeError) as e:
            # Em caso de erro, retornar lista vazia
            return []

    async def list_tipos(self, **filters: Any) -> List[TipoOS]:
        try:
            data = await self._get_all_pages("/api/v3/tipo_ordem_servico/", filters)
            return [TipoOS.model_validate(item) for item in data]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Endpoint não existe, retornar dados padrão
                return [
                    TipoOS(id=1, descricao="Corretiva"),
                    TipoOS(id=2, descricao="Preventiva"),
                    TipoOS(id=3, descricao="Busca Ativa"),
                ]
            raise
        except (httpx.RequestError, ConnectionError, RuntimeError) as e:
            # Em caso de erro de conexão, retornar dados padrão
            return [
                TipoOS(id=1, descricao="Corretiva"),
                TipoOS(id=2, descricao="Preventiva"),
                TipoOS(id=3, descricao="Busca Ativa"),
            ]

    async def list_estados(self, **filters: Any) -> List[EstadoOS]:
        try:
            data = await self._get_all_pages("/api/v3/estado_os/", filters)
            return [EstadoOS.model_validate(item) for item in data]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Endpoint não existe, retornar dados padrão
                return [
                    EstadoOS(id=1, descricao="Aberta"),
                    EstadoOS(id=4, descricao="Fechada"),
                    EstadoOS(id=5, descricao="Cancelada"),
                ]
            raise
        except (httpx.RequestError, ConnectionError, RuntimeError) as e:
            # Em caso de erro de conexão, retornar dados padrão
            return [
                EstadoOS(id=1, descricao="Aberta"),
                EstadoOS(id=4, descricao="Fechada"),
                EstadoOS(id=5, descricao="Cancelada"),
            ]