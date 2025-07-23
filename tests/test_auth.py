import asyncio
from datetime import datetime, timedelta, timezone

import pytest
import httpx
from httpx import Response, Request, MockTransport

from app.arkmeds_client.auth import ArkmedsAuth, ArkmedsAuthError, TokenData


class DummyAuth(ArkmedsAuth):
    """ArkmedsAuth with custom transport for testing."""

    def __init__(self, transport: MockTransport) -> None:
        super().__init__(email="a", password="b", base_url="https://api.test")
        self._client = httpx.AsyncClient(base_url=self.base_url, transport=transport)


@pytest.mark.asyncio
async def test_login_success_without_trailing_slash():
    async def handler(request: Request) -> Response:
        if request.url.path == "/api/v3/auth/login":
            return Response(
                200,
                json={"token": "x"},
            )
        return Response(404)

    auth = DummyAuth(MockTransport(handler))
    data = await auth.login()
    assert isinstance(data, TokenData)
    assert data.token == "x"


class OldAuth(ArkmedsAuth):
    async def login(self) -> TokenData:  # type: ignore[override]
        client = await self._get_client()
        resp = await client.post(
            "/api/v3/auth/login/",
            json={"email": self.email, "password": self.password},
            timeout=10,
        )
        resp.raise_for_status()
        exp = datetime.now(timezone.utc) + timedelta(hours=1)
        token = resp.json().get("token")
        if not token:
            raise ArkmedsAuthError("Malformed login response")
        self._token = TokenData(token=token, exp=exp)
        return self._token


@pytest.mark.asyncio
async def test_login_with_trailing_slash_returns_404():
    async def handler(request: Request) -> Response:
        assert request.url.path == "/api/v3/auth/login/"
        return Response(404)

    auth = OldAuth(email="a", password="b", base_url="https://api.test")
    auth._client = httpx.AsyncClient(base_url=auth.base_url, transport=MockTransport(handler))
    with pytest.raises(httpx.HTTPStatusError):
        await auth.login()


