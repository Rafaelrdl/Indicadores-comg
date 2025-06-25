from dataclasses import dataclass
from typing import Optional


@dataclass
class OrderService:
    """Represents a maintenance order."""

    tipo_servico: str
    estado: str
    quadro_trabalho: str
    prioridade: str
    estado_tempo_atendimento: Optional[str] = None
    estado_tempo_fechamento: Optional[str] = None
