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
    ABERTA = 1
    FECHADA = 4
    CANCELADA = 5


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
    ativo: bool
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
    responsavel: int | None = None  # ID do responsável, não o objeto User completo
    data_criacao: datetime = Field(alias="data_criacao")
    data_fechamento: datetime | None = Field(default=None, alias="data_fechamento")
    equipamento: dict | None = None  # Objeto equipamento completo
    is_active: bool | None = None
    observacoes: str | None = None
    solicitante: dict | None = None
    origem: int | None = None
    descricao_servico: str | None = None

    @property
    def equipamento_id(self) -> int | None:
        """Retorna o ID do equipamento a partir do objeto equipamento."""
        if self.equipamento and isinstance(self.equipamento, dict):
            return self.equipamento.get('id')
        return None

    @field_validator("data_criacao", "data_fechamento", mode="before")
    @classmethod
    def _parse_dt(cls, v: str | datetime | None) -> datetime | None:
        if v is None or isinstance(v, datetime):
            return v
        return datetime.strptime(v, "%d/%m/%y - %H:%M")