"""
Repositório de dados para acesso ao SQLite local.

Este módulo fornece acesso otimizado aos dados locais,
substituindo chamadas diretas à API durante navegação.
"""

import json
from typing import Any

import pandas as pd
import streamlit as st

from app.core.db import get_conn
from app.core.logging import app_logger


# ========== FUNÇÕES DE QUERY GENÉRICAS ==========


def query_df(sql: str, params: tuple = ()) -> pd.DataFrame:
    """
    Executa query SQL e retorna DataFrame.

    Args:
        sql: Query SQL para executar
        params: Parâmetros para a query

    Returns:
        DataFrame com resultados
    """
    try:
        with get_conn() as conn:
            return pd.read_sql_query(sql, conn, params=params)
    except Exception as e:
        app_logger.log_error(f"Erro na query SQL: {e}")
        return pd.DataFrame()


def query_single_value(sql: str, params: tuple = ()) -> Any:
    """
    Executa query e retorna valor único.

    Args:
        sql: Query SQL
        params: Parâmetros

    Returns:
        Valor único ou None
    """
    try:
        with get_conn() as conn:
            cursor = conn.execute(sql, params)
            result = cursor.fetchone()
            return result[0] if result else None
    except Exception as e:
        app_logger.log_error(f"Erro na query de valor único: {e}")
        return None


# ========== FUNÇÕES CACHED PARA PÁGINAS ==========


@st.cache_data(ttl=60)  # Cache de 1 minuto para reduzir I/O
def get_orders_df(
    start_date: str | None = None,
    end_date: str | None = None,
    estados: list[int] | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    """
    Busca ordens de serviço do banco local com filtros.

    Args:
        start_date: Data inicial (ISO format)
        end_date: Data final (ISO format)
        estados: Lista de estados para filtrar
        limit: Limite de registros

    Returns:
        DataFrame com ordens formatadas para UI
    """
    # Query base extraindo campos do JSON
    sql = """
        SELECT
            json_extract(payload, '$.id') as id,
            json_extract(payload, '$.chamados') as chamados,
            json_extract(payload, '$.data_criacao') as data_criacao,
            json_extract(payload, '$.data_fechamento') as data_fechamento,
            json_extract(payload, '$.ordem_servico') as ordem_servico,
            json_extract(payload, '$.responsavel_id') as responsavel_id,
            json_extract(payload, '$.ordem_servico.estado') as estado,
            json_extract(payload, '$.ordem_servico.numero') as numero,
            json_extract(payload, '$.ordem_servico.tipo_servico') as tipo_servico,
            updated_at,
            fetched_at,
            payload
        FROM orders
        WHERE 1=1
    """

    params = []

    # Aplicar filtros
    if start_date:
        sql += " AND json_extract(payload, '$.data_criacao') >= ?"
        params.append(start_date)

    if end_date:
        sql += " AND json_extract(payload, '$.data_criacao') <= ?"
        params.append(end_date)

    if estados:
        placeholders = ",".join(["?" for _ in estados])
        sql += f" AND json_extract(payload, '$.ordem_servico.estado') IN ({placeholders})"
        params.extend(estados)

    # Ordenar por data de criação (mais recentes primeiro)
    sql += " ORDER BY json_extract(payload, '$.data_criacao') DESC"

    if limit:
        sql += f" LIMIT {limit}"

    df = query_df(sql, tuple(params))

    # Processar colunas JSON se necessário
    if not df.empty:
        # Parse ordem_servico JSON se for string
        if "ordem_servico" in df.columns:
            df["ordem_servico"] = df["ordem_servico"].apply(
                lambda x: json.loads(x) if isinstance(x, str) else x
            )

    app_logger.log_info(f"📊 Carregadas {len(df):,} ordens do SQLite local")
    return df


@st.cache_data(ttl=60)
def get_equipments_df(limit: int | None = None, search: str | None = None) -> pd.DataFrame:
    """
    Busca equipamentos do banco local.

    Args:
        limit: Limite de registros
        search: Termo para buscar na descrição

    Returns:
        DataFrame com equipamentos
    """
    sql = """
        SELECT
            json_extract(payload, '$.id') as id,
            json_extract(payload, '$.descricao') as descricao,
            json_extract(payload, '$.fabricante') as fabricante,
            json_extract(payload, '$.modelo') as modelo,
            json_extract(payload, '$.proprietario') as proprietario,
            updated_at,
            fetched_at,
            payload
        FROM equipments
        WHERE 1=1
    """

    params = []

    if search:
        sql += " AND json_extract(payload, '$.descricao') LIKE ?"
        params.append(f"%{search}%")

    sql += " ORDER BY json_extract(payload, '$.descricao')"

    if limit:
        sql += f" LIMIT {limit}"

    df = query_df(sql, tuple(params))
    app_logger.log_info(f"🔧 Carregados {len(df):,} equipamentos do SQLite local")
    return df


@st.cache_data(ttl=60)
def get_technicians_df(limit: int | None = None) -> pd.DataFrame:
    """
    Busca técnicos do banco local.

    Args:
        limit: Limite de registros

    Returns:
        DataFrame com técnicos
    """
    sql = """
        SELECT
            json_extract(payload, '$.id') as id,
            json_extract(payload, '$.nome') as nome,
            json_extract(payload, '$.email') as email,
            json_extract(payload, '$.ativo') as ativo,
            updated_at,
            fetched_at,
            payload
        FROM technicians
        WHERE 1=1
        ORDER BY json_extract(payload, '$.nome')
    """

    if limit:
        sql += f" LIMIT {limit}"

    df = query_df(sql, ())
    app_logger.log_info(f"👥 Carregados {len(df):,} técnicos do SQLite local")
    return df


# ========== QUERIES ESPECÍFICAS PARA MÉTRICAS ==========


@st.cache_data(ttl=30)  # Cache mais curto para métricas
def get_orders_by_state_counts() -> dict[int, int]:
    """
    Conta ordens por estado.

    Returns:
        Dict {estado: contagem}
    """
    sql = """
        SELECT
            json_extract(payload, '$.ordem_servico.estado') as estado,
            COUNT(*) as total
        FROM orders
        WHERE json_extract(payload, '$.ordem_servico.estado') IS NOT NULL
        GROUP BY json_extract(payload, '$.ordem_servico.estado')
    """

    df = query_df(sql)
    if df.empty:
        return {}

    return dict(zip(df["estado"].astype(int), df["total"], strict=False))


@st.cache_data(ttl=30)
def get_orders_by_type_counts() -> dict[int, int]:
    """
    Conta ordens por tipo de serviço.

    Returns:
        Dict {tipo: contagem}
    """
    sql = """
        SELECT
            json_extract(payload, '$.ordem_servico.tipo_servico') as tipo,
            COUNT(*) as total
        FROM orders
        WHERE json_extract(payload, '$.ordem_servico.tipo_servico') IS NOT NULL
        GROUP BY json_extract(payload, '$.ordem_servico.tipo_servico')
    """

    df = query_df(sql)
    if df.empty:
        return {}

    return dict(zip(df["tipo"].astype(int), df["total"], strict=False))


@st.cache_data(ttl=30)
def get_orders_timeline_data(
    start_date: str | None = None, end_date: str | None = None
) -> pd.DataFrame:
    """
    Dados para timeline de ordens (gráficos temporais).

    Args:
        start_date: Data inicial
        end_date: Data final

    Returns:
        DataFrame com dados agrupados por data
    """
    sql = """
        SELECT
            DATE(json_extract(payload, '$.data_criacao')) as data,
            json_extract(payload, '$.ordem_servico.estado') as estado,
            json_extract(payload, '$.ordem_servico.tipo_servico') as tipo,
            COUNT(*) as total
        FROM orders
        WHERE json_extract(payload, '$.data_criacao') IS NOT NULL
    """

    params = []

    if start_date:
        sql += " AND DATE(json_extract(payload, '$.data_criacao')) >= ?"
        params.append(start_date)

    if end_date:
        sql += " AND DATE(json_extract(payload, '$.data_criacao')) <= ?"
        params.append(end_date)

    sql += """
        GROUP BY
            DATE(json_extract(payload, '$.data_criacao')),
            json_extract(payload, '$.ordem_servico.estado'),
            json_extract(payload, '$.ordem_servico.tipo_servico')
        ORDER BY data DESC
    """

    df = query_df(sql, tuple(params))
    app_logger.log_info(f"📈 Timeline data: {len(df):,} pontos carregados")
    return df


# ========== FUNÇÕES DE ESTATÍSTICAS ==========


@st.cache_data(ttl=30)
def get_database_stats() -> dict[str, Any]:
    """
    Estatísticas do banco de dados local.

    Returns:
        Dict com estatísticas
    """
    stats = {}

    # Contar registros por tabela
    for table in ["orders", "equipments", "technicians"]:
        count = query_single_value(f"SELECT COUNT(*) FROM {table}")
        stats[f"{table}_count"] = count or 0

    # Última sincronização - usar schema atualizado
    last_sync_sql = """
        SELECT resource, synced_at, total_records, sync_type, last_updated_at
        FROM sync_state
        ORDER BY COALESCE(synced_at, updated_at) DESC
        LIMIT 3
    """

    try:
        sync_df = query_df(last_sync_sql)
        stats["last_syncs"] = sync_df.to_dict("records") if not sync_df.empty else []
    except Exception:
        # Fallback para schema antigo se necessário
        try:
            fallback_sql = "SELECT resource, updated_at, total_records FROM sync_state ORDER BY updated_at DESC LIMIT 3"
            sync_df = query_df(fallback_sql)
            stats["last_syncs"] = sync_df.to_dict("records") if not sync_df.empty else []
        except:
            stats["last_syncs"] = []

    # Tamanho do banco
    db_size = query_single_value(
        "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()"
    )
    stats["database_size_bytes"] = db_size or 0
    stats["database_size_mb"] = round((db_size or 0) / 1024 / 1024, 2)

    return stats


# ========== COMPATIBILIDADE COM SISTEMA ANTIGO ==========


class Repository:
    """Classe de compatibilidade com sistema antigo."""

    @staticmethod
    def get_orders(estados: list[int] | None = None, limit: int | None = None) -> pd.DataFrame:
        """Compatibilidade com método antigo."""
        return get_orders_df(estados=estados, limit=limit)

    @staticmethod
    def get_equipments(limit: int | None = None) -> pd.DataFrame:
        """Compatibilidade com método antigo."""
        return get_equipments_df(limit=limit)

    @staticmethod
    def get_technicians(limit: int | None = None) -> pd.DataFrame:
        """Compatibilidade com método antigo."""
        return get_technicians_df(limit=limit)

    @staticmethod
    def save_orders(records: list[dict[str, Any]]) -> int:
        """Compatibilidade - usar sync system."""
        from app.services.sync._upsert import upsert_records

        conn = get_conn()
        return upsert_records(conn, "orders", records)

    @staticmethod
    def save_equipments(records: list[dict[str, Any]]) -> int:
        """Compatibilidade - usar sync system."""
        from app.services.sync._upsert import upsert_records

        conn = get_conn()
        return upsert_records(conn, "equipments", records)

    @staticmethod
    def save_technicians(records: list[dict[str, Any]]) -> int:
        """Compatibilidade - usar sync system."""
        from app.services.sync._upsert import upsert_records

        conn = get_conn()
        return upsert_records(conn, "technicians", records)

    @staticmethod
    def update_sync_state(resource: str, **kwargs) -> None:
        """Compatibilidade - usar sync system."""
        from app.services.sync._upsert import update_sync_state

        conn = get_conn()
        update_sync_state(conn, resource, **kwargs)

    @staticmethod
    def get_sync_state(resource: str) -> dict[str, Any] | None:
        """Compatibilidade - usar sync system."""
        from app.services.sync._upsert import get_last_sync_info

        conn = get_conn()
        return get_last_sync_info(conn, resource)

    @staticmethod
    def is_data_fresh(resource: str, max_age_hours: int = 2) -> bool:
        """Compatibilidade - usar sync system."""
        from app.services.sync.delta import should_run_incremental_sync

        return not should_run_incremental_sync(resource, max_age_hours)
