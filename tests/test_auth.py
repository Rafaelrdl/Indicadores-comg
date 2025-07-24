import httpx
import pytest
from httpx import MockTransport, Request, Response

from app.arkmeds_client.auth import ArkmedsAuth, TokenData


class DummyAuth(ArkmedsAuth):
    """ArkmedsAuth with custom transport for testing."""

    def __init__(self, transport: MockTransport) -> None:
        super().__init__(email="a", password="b", base_url="https://api.test")
        self._client = httpx.AsyncClient(base_url=self.base_url, transport=transport)


@pytest.mark.asyncio
async def test_login_success_without_trailing_slash():
    async def handler(request: Request) -> Response:
        if request.method in ("HEAD", "OPTIONS") and request.url.path == "/api/v3/auth/login":
            return Response(204)
        if request.method == "POST" and request.url.path == "/api/v3/auth/login":
            return Response(200, json={"token": "x"})
        return Response(404)

    auth = DummyAuth(MockTransport(handler))
    data = await auth.login()
    assert isinstance(data, TokenData)
    assert data.token == "x"


@pytest.mark.asyncio
async def test_login_fallback_on_404():
    calls_head = []
    calls_post = []

    async def handler(request: Request) -> Response:
        if request.method in ("HEAD", "OPTIONS"):
            calls_head.append(request.url.path)
            if request.url.path == "/api/v3/auth/login":
                return Response(404)
            if request.url.path == "/api/v3/login":
                return Response(204)
            return Response(404)
        calls_post.append(request.url.path)
        if request.url.path == "/api/v3/login":
            return Response(200, json={"token": "y"})
        return Response(404)

    auth = DummyAuth(MockTransport(handler))
    data = await auth.login()
    assert data.token == "y"
    assert auth._login_url == "/api/v3/login"

    await auth.login()
    assert "/api/v3/auth/login" in calls_head
    assert calls_post == ["/api/v3/login", "/api/v3/login"]


