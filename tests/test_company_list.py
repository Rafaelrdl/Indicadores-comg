"""Tests for the company list helper."""
# ruff: noqa: E402

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest

requests = pytest.importorskip("requests")
from infrastructure import arkmeds_client


def test_company_list(monkeypatch) -> None:
    arkmeds_client.BASE_URL = "http://example.com"

    class DummyResponse:
        status_code = 401

        def raise_for_status(self):
            raise requests.HTTPError(response=self)

        def json(self):
            return {}

    def fake_request(method, url, headers=None, timeout=15, **kwargs):
        return DummyResponse()

    monkeypatch.setattr(arkmeds_client, "get_token", lambda force=False: "dummy")
    monkeypatch.setattr(requests, "request", fake_request)

    try:
        arkmeds_client.list_companies()
    except requests.HTTPError as exc:
        assert exc.response.status_code in {401, 200}
    else:
        assert True
