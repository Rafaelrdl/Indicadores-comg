from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest

pytest.importorskip("requests")
from infrastructure.arkmeds_client import ROUTES


def test_routes_start_with_api() -> None:
    for path in ROUTES.values():
        assert path.startswith("/api/")
