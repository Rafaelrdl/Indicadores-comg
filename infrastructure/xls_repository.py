"""Repository to load order services from an Excel file."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

import pandas as pd

from domain.entities import OrderService


class OrderServiceXLSRepository:
    """Load :class:`OrderService` entries from an Excel file."""

    def __init__(self, file_path: Path) -> None:
        """Initialize repository.

        Args:
            file_path: Caminho para o arquivo XLS a ser lido.
        """
        self._file_path = file_path

    def load(self) -> List[OrderService]:
        """Return all orders from the Excel file.

        Returns:
            Lista de :class:`OrderService` carregadas do arquivo.
        """
        ext = os.path.splitext(self._file_path)[1].lower()
        engine = "xlrd" if ext == ".xls" else "openpyxl"
        df = pd.read_excel(self._file_path, engine=engine)
        df = df.where(pd.notnull(df), None)
        orders = []
        for row in df.to_dict(orient="records"):
            orders.append(
                OrderService(
                    tipo_servico=row.get("TIPO SERVIÇO", ""),
                    estado=row.get("ESTADO", ""),
                    quadro_trabalho=row.get("QUADRO DE TRABALHO", ""),
                    prioridade=row.get("PRIORIDADE", ""),
                    estado_tempo_atendimento=row.get("Estado tempo atendimento"),
                    estado_tempo_fechamento=row.get("Estado tempo fechamento"),
                )
            )
        return orders
