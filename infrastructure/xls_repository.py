"""Repository to load order services from an XLS file.

The expected format is a text-based spreadsheet exported from Excel using comma
separated values. The file may use the ``.xls`` extension even though it is not
an actual binary Excel file.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import List

from domain.entities import OrderService


class OrderServiceXLSRepository:
    """Load :class:`OrderService` entries from a pseudo-XLS file."""

    def __init__(self, file_path: Path) -> None:
        """Initialize repository.

        Args:
            file_path: Caminho para o arquivo XLS a ser lido.
        """
        self._file_path = file_path

    def load(self) -> List[OrderService]:
        """Return all orders from the XLS file.

        Returns:
            Lista de :class:`OrderService` carregadas do arquivo.
        """
        orders: List[OrderService] = []
        with self._file_path.open(newline="", encoding="utf-8") as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                orders.append(
                    OrderService(
                        tipo_servico=row.get("TIPO SERVI\xc7O", ""),
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
