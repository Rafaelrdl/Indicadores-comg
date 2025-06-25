from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from application.metrics import count_orders, percentage
from domain.entities import OrderService
from infrastructure.xls_repository import OrderServiceXLSRepository


def load_sample() -> list[OrderService]:
    repo = OrderServiceXLSRepository(Path("tests/fixtures/sample_orders.xls"))
    return repo.load()


def test_count_orders() -> None:
    orders = load_sample()
    assert count_orders(orders, tipo_servico="Manutenção Corretiva") == 2
    assert (
        count_orders(orders, tipo_servico="Manutenção Corretiva", estado="Fechada") == 1
    )


def test_percentage() -> None:
    assert percentage(50, 200) == 25.0
    assert percentage(0, 0) == 0.0
