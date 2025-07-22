from datetime import datetime, timedelta, timezone
import asyncio

import httpx
from httpx import Response, Request
from httpx import MockTransport

from app.arkmeds_client.auth import ArkmedsAuth
from app.arkmeds_client.client import ArkmedsClient
from app.arkmeds_client.models import TokenData


class DummyAuth(ArkmedsAuth):
    def __init__(self) -> None:
        super().__init__(email="a", password="b", base_url="https://api.test")

    async def login(self) -> TokenData:  # type: ignore[override]
        self._token = TokenData(
            token="x",
            exp=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        return self._token

    async def refresh(self) -> None:  # type: ignore[override]
        return


def make_client(responses):
    async def handler(request: Request) -> Response:
        path = request.url.path
        query = request.url.query.decode()
        if path == "/api/v3/ordem_servico/" and "page=2" in query:
            return responses.pop("/api/v3/ordem_servico/?page=2")
        return responses.pop("/api/v3/ordem_servico/")

    transport = MockTransport(handler)
    auth = DummyAuth()
    client = ArkmedsClient(auth)
    client._client = httpx.AsyncClient(base_url=auth.base_url, transport=transport)
    return client


def test_paginated_success():
    responses = {
        "/api/v3/ordem_servico/": Response(
            200,
            json={
                "count": 3,
                "next": "https://api.test/api/v3/ordem_servico/?page=2",
                "results": [{"id": 1}],
            },
        ),
        "/api/v3/ordem_servico/?page=2": Response(
            200,
            json={"count": 3, "next": None, "results": [{"id": 2}, {"id": 3}]},
        ),
    }
    client = make_client(responses)
    data = asyncio.run(client.list_os())
    assert len(data) == 3


def test_401_refresh_once():
    responses = {
        "/api/v3/ordem_servico/": Response(401),
        "retry": Response(
            200,
            json={"count": 1, "next": None, "results": [{"id": 1}]},
        ),
    }

    async def handler(request: Request) -> Response:
        path = request.url.raw_path.decode()
        if path == "/api/v3/ordem_servico/" and not getattr(handler, "called", False):
            handler.called = True
            return responses[path]
        return responses["retry"]

    transport = MockTransport(handler)
    auth = DummyAuth()
    client = ArkmedsClient(auth)
    client._client = httpx.AsyncClient(base_url=auth.base_url, transport=transport)
    data = asyncio.run(client.list_os())
    assert len(data) == 1


def test_retry_5xx():
    calls = []

    async def handler(request: Request) -> Response:
        calls.append(1)
        if len(calls) < 3:
            return Response(500)
        return Response(
            200,
            json={"count": 1, "next": None, "results": [{"id": 1}]},
        )

    transport = MockTransport(handler)
    auth = DummyAuth()
    client = ArkmedsClient(auth, max_retries=3)
    client._client = httpx.AsyncClient(base_url=auth.base_url, transport=transport)
    data = asyncio.run(client.list_os())
    assert len(data) == 1
    assert len(calls) == 3


def test_filters_in_query():
    async def handler(request: Request) -> Response:
        assert b"estado=4" in request.url.query
        return Response(200, json={"count": 0, "next": None, "results": []})

    transport = MockTransport(handler)
    auth = DummyAuth()
    client = ArkmedsClient(auth)
    client._client = httpx.AsyncClient(base_url=auth.base_url, transport=transport)
    asyncio.run(client.list_os(estado=4))
