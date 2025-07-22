from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import httpx
from aiolimiter import AsyncLimiter

from .auth import ArkmedsAuth
from .models import OS, Equipment, PaginatedResponse, User


class ArkmedsClient:
    def __init__(
        self,
        auth: ArkmedsAuth,
        *,
        timeout: float = 5.0,
        max_retries: int = 3,
        rate: int = 10,
    ) -> None:
        self.auth = auth
        self.timeout = timeout
        self.max_retries = max_retries
        self.limiter = AsyncLimiter(max_rate=rate, time_period=1)
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if not self._client:
            token = await self.auth.get_token()
            headers = {"Authorization": f"Bearer {token}"}
            self._client = httpx.AsyncClient(
                base_url=self.auth.base_url, timeout=self.timeout, headers=headers
            )
        return self._client

    async def _request(
        self, method: str, url: str, *, params: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        client = await self._get_client()
        for attempt in range(self.max_retries):
            try:
                async with self.limiter:
                    resp = await client.request(method, url, params=params)
                if resp.status_code == 401 and attempt == 0:
                    await self.auth.login()
                    client.headers["Authorization"] = f"Bearer {await self.auth.get_token()}"
                    continue
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
        while url:
            resp = await self._request("GET", url, params=params if url == endpoint else None)
            data = PaginatedResponse.model_validate(resp.json())
            results.extend(data.results)
            url = data.next
            params = None
        return results

    async def list_os(self, **filters: Any) -> List[OS]:
        data = await self._get_all_pages("/api/v3/ordem_servico/", filters)
        return [OS.model_validate(item) for item in data]

    async def list_equipment(self, **filters: Any) -> List[Equipment]:
        data = await self._get_all_pages("/api/v3/equipamento/", filters)
        return [Equipment.model_validate(item) for item in data]

    async def list_users(self, **filters: Any) -> List[User]:
        data = await self._get_all_pages("/api/v3/users/", filters)
        return [User.model_validate(item) for item in data]

