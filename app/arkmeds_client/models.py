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
    tipo: TipoOS = Field(alias="tipo_ordem_servico")
    estado: EstadoOS = Field(alias="estado")
    responsavel: User | None = None
    created_at: datetime = Field(alias="data_criacao")
    closed_at: datetime | None = Field(default=None, alias="data_fechamento")

    @field_validator("created_at", "closed_at", mode="before")
    @classmethod
    def _parse_dt(cls, v: str | datetime | None) -> datetime | None:
        if v is None or isinstance(v, datetime):
            return v
        return datetime.strptime(v, "%d/%m/%y - %H:%M")
