from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TokenData(BaseModel):
    token: str
    exp: datetime


class PaginatedResponse(BaseModel):
    count: int
    next: str | None = None
    results: list[dict]


class ArkBase(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class OSEstado(Enum):
    """Estados possíveis de Ordem de Serviço.
    
    ⚡ AUDITORIA REALIZADA: 24/07/2025
    📡 Fonte: Consulta à API /api/v3/estado_ordem_servico/
    📊 Total encontrado: 22 estados únicos
    🔍 Método: Consulta direta + análise de OSs em produção
    
    NOTA: Alguns estados (IDs 20, 21, 22) têm descrição apenas "." 
    na API, possivelmente estados de teste ou reservados.
    """
    # Estados principais
    ABERTA = 1
    FECHADA = 2
    CANCELADA = 3
    EM_EXECUCAO = 4
    
    # Estados de espera/pendência
    AGUARDANDO_PECAS = 5
    AGUARDANDO_APROVACAO_ORCAMENTO = 6
    AGUARDANDO_ORCAMENTO = 12
    AGUARDANDO_ANEXO_CERTIFICADOS = 13
    AGUARDANDO_ANALISE_CRITICA = 14
    AGUARDANDO_PROGRAMACAO = 18
    AGUARDANDO_ANALISE = 19
    EM_ESPERA = 11
    
    # Estados de conclusão/finalização
    SERVICO_FINALIZADO = 7
    ANALISE_CONCLUIDA = 8
    ORCAMENTO_APROVADO = 10
    
    # Estados de manutenção/reparo
    EM_MANUTENCAO = 16
    REPARO_EXTERNO = 9
    AGENDADA_FABRICANTE_CONTRATADO = 15
    SERVICO_CORRETIVA_PROGRAMADO = 17
    
    # Estados especiais/diversos
    ESTADO_ESPECIAL_1 = 20  # Descrição: "."
    ESTADO_ESPECIAL_2 = 21  # Descrição: "."
    ESTADO_ESPECIAL_3 = 22  # Descrição: "."
    
    @classmethod
    def estados_abertos(cls) -> list["OSEstado"]:
        """Retorna estados considerados 'abertos' (OS ainda em andamento)."""
        return [
            cls.ABERTA,
            cls.EM_EXECUCAO,
            cls.AGUARDANDO_PECAS,
            cls.AGUARDANDO_APROVACAO_ORCAMENTO,
            cls.AGUARDANDO_ORCAMENTO,
            cls.AGUARDANDO_ANEXO_CERTIFICADOS,
            cls.AGUARDANDO_ANALISE_CRITICA,
            cls.AGUARDANDO_PROGRAMACAO,
            cls.AGUARDANDO_ANALISE,
            cls.EM_ESPERA,
            cls.EM_MANUTENCAO,
            cls.REPARO_EXTERNO,
            cls.AGENDADA_FABRICANTE_CONTRATADO,
            cls.SERVICO_CORRETIVA_PROGRAMADO,
        ]
    
    @classmethod
    def estados_fechados(cls) -> list["OSEstado"]:
        """Retorna estados considerados 'fechados' (OS concluída)."""
        return [
            cls.FECHADA,
            cls.SERVICO_FINALIZADO,
            cls.ANALISE_CONCLUIDA,
            cls.ORCAMENTO_APROVADO,
        ]
    
    @classmethod
    def estados_cancelados(cls) -> list["OSEstado"]:
        """Retorna estados considerados 'cancelados'."""
        return [cls.CANCELADA]
    
    @classmethod
    def get_descricao(cls, estado_id: int) -> str:
        """Retorna descrição amigável do estado baseado no ID."""
        descricoes = {
            1: "Aberta",
            2: "Fechada", 
            3: "Cancelada",
            4: "Em execução",
            5: "Aguardando peças",
            6: "Aguardando aprovação do orçamento",
            7: "Serviço finalizado",
            8: "Análise concluída",
            9: "Reparo externo",
            10: "Orçamento Aprovado",
            11: "Em Espera",
            12: "Aguardando Orçamento",
            13: "Aguardando anexo de Certificados",
            14: "Aguardando Análise Crítica",
            15: "Agendada para o Fabricante ou Contratado",
            16: "Em Manutenção",
            17: "Serviço de manutenção corretiva programado",
            18: "Aguardando programação",
            19: "Aguardando analise",
            20: "Estado especial 1",
            21: "Estado especial 2", 
            22: "Estado especial 3",
        }
        return descricoes.get(estado_id, f"Estado desconhecido ({estado_id})")


class TipoOS(ArkBase):
    id: int
    descricao: str = Field(alias="descricao")


class EstadoOS(ArkBase):
    id: int
    descricao: str


class User(ArkBase):
    id: int
    nome: str
    email: str
    cargo: str | None = None


class Equipment(ArkBase):
    id: int
    nome: str
    ativo: bool | None = None
    data_aquisicao: datetime | None = Field(default=None, alias="data_aquisicao")

    @field_validator("data_aquisicao", mode="before")
    @classmethod
    def _parse_date(cls, v: str | datetime | None) -> datetime | None:
        if v is None or isinstance(v, datetime):
            return v
        return datetime.strptime(v, "%d/%m/%y - %H:%M")


class OS(ArkBase):
    id: int
    numero: str | None = None
    tipo_servico: int | None = Field(default=None, alias="tipo_servico")
    estado: dict | None = None  # Estrutura: {"id": int, "descricao": str, "pode_visualizar": bool}
    responsavel: User | None = None
    data_criacao: datetime = Field(alias="data_criacao")
    data_fechamento: datetime | None = Field(default=None, alias="data_fechamento")
    equipamento: dict | None = None  # Objeto equipamento completo
    equipamento_id: int | None = Field(default=None, alias="equipamento_id")
    is_active: bool | None = None
    observacoes: str | None = None
    solicitante: dict | None = None
    origem: int | None = None
    descricao_servico: str | None = None

    @field_validator("data_criacao", "data_fechamento", mode="before")
    @classmethod
    def _parse_dt(cls, v: str | datetime | None) -> datetime | None:
        if v is None or isinstance(v, datetime):
            return v
        return datetime.strptime(v, "%d/%m/%y - %H:%M")

    @field_validator("responsavel", mode="before")
    @classmethod
    def _parse_user(cls, v: int | dict | None) -> User | None:
        if v is None or isinstance(v, User):
            return v
        if isinstance(v, dict):
            return User.model_validate(v)
        return User(id=v, nome="", email="")

    @property
    def created_at(self) -> datetime:
        return self.data_criacao

    @property
    def closed_at(self) -> datetime | None:
        return self.data_fechamento
