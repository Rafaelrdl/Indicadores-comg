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

    tipo_servico: str
    estado: str
    quadro_trabalho: str
    prioridade: str
    estado_tempo_atendimento: Optional[str] = None
    estado_tempo_fechamento: Optional[str] = None
