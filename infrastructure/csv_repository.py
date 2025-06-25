"""Repository to load order services from a CSV file."""

import csv
from pathlib import Path
from typing import List

from domain.entities import OrderService


class OrderServiceCSVRepository:
    """Load :class:`OrderService` entries from a CSV file."""

    def __init__(self, file_path: Path) -> None:
        """Initialize repository.

        Args:
            file_path: Caminho para o arquivo CSV a ser lido.
        """
        self._file_path = file_path

    def load(self) -> List[OrderService]:
        """Return all orders from the CSV file.

        Returns:
            Lista de :class:`OrderService` carregadas do CSV.
        """
        orders: List[OrderService] = []
        with self._file_path.open(newline="", encoding="utf-8") as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                orders.append(
                    OrderService(
                        tipo_servico=row.get("TIPO SERVIÇO", ""),
                        estado=row.get("ESTADO", ""),
                        quadro_trabalho=row.get("QUADRO DE TRABALHO", ""),
                        prioridade=row.get("PRIORIDADE", ""),
                        estado_tempo_atendimento=row.get(
                            "Estado tempo atendimento", ""
                        ),
                        estado_tempo_fechamento=row.get("Estado tempo fechamento", ""),
                    )
                )
        return orders
