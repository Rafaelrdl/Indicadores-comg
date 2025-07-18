"""Ensure the authorization prefix is applied."""
# ruff: noqa: E402

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest

requests = pytest.importorskip("requests")
from infrastructure import arkmeds_client


def test_auth_prefix(monkeypatch) -> None:
    arkmeds_client.AUTH_PREFIX = "JWT"

    def fake_request(method, url, headers=None, timeout=15, **kwargs):
        fake_request.captured = headers

        class DummyResp:
            status_code = 200

            def raise_for_status(self):
                pass

            def json(self):
                return {}

        return DummyResp()

    monkeypatch.setattr(arkmeds_client, "get_token", lambda force=False: "abc.def.ghi")
    monkeypatch.setattr(requests, "request", fake_request)

    arkmeds_client._request("GET", "company/")
    assert fake_request.captured["Authorization"].startswith("JWT ")
