"""Core domain entities used throughout the application."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class OrderService:
    """Represents a maintenance order.

    Attributes:
        tipo_servico: Tipo de serviço executado.
        estado: Estado atual da ordem (Aberta ou Fechada).
        quadro_trabalho: Área responsável pela execução.
        prioridade: Grau de prioridade.
        estado_tempo_atendimento: Situação do tempo de atendimento.
        estado_tempo_fechamento: Situação do tempo de fechamento.
    """

    # Tipo de serviço executado (corretiva, preventiva etc.)
    tipo_servico: str
    # Situação atual da ordem de serviço
    estado: str
    # Área ou departamento responsável pela execução
    quadro_trabalho: str
    # Grau de prioridade definido para a ordem
    prioridade: str
    # Avaliação do tempo gasto até iniciar o atendimento
    estado_tempo_atendimento: Optional[str] = None
    # Avaliação do tempo gasto até o fechamento da ordem
    estado_tempo_fechamento: Optional[str] = None
