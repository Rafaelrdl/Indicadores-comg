"""
Módulo de conexão e configuração do banco SQLite.

Este módulo fornece conexão singleton para SQLite com configurações
otimizadas para performance e confiabilidade.
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Optional

import streamlit as st


# Configurações do banco
DB_PATH = Path("data") / "app.db"
DB_TIMEOUT = 30.0  # Timeout em segundos


@st.cache_resource
def get_conn() -> sqlite3.Connection:
    """
    Retorna conexão singleton com SQLite configurada para performance.
    
    Configurações aplicadas:
    - WAL mode: melhor concorrência e performance
    - NORMAL synchronous: balanceio entre performance e segurança
    - Timeout de 30s para operações
    """
    # Garantir que o diretório data existe
    DB_PATH.parent.mkdir(exist_ok=True)
    
    # Criar conexão com configurações otimizadas
    conn = sqlite3.connect(
        str(DB_PATH), 
        check_same_thread=False,
        timeout=DB_TIMEOUT
    )
    
    # Configurações de performance e confiabilidade
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;") 
    conn.execute("PRAGMA temp_store=MEMORY;")
    conn.execute("PRAGMA mmap_size=268435456;")  # 256MB
    
    # Habilitar foreign keys
    conn.execute("PRAGMA foreign_keys=ON;")
    
    # Configurar row factory para acessar colunas por nome
    conn.row_factory = sqlite3.Row
    
    return conn


def init_database() -> None:
    """
    Inicializa o banco de dados criando tabelas e índices necessários.
    """
    conn = get_conn()
    
    try:
        # Tabela de ordens de serviço/chamados
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                payload TEXT NOT NULL,  -- JSON serializado
                updated_at TEXT,        -- Data de atualização do registro
                fetched_at INTEGER NOT NULL,  -- Timestamp da busca
                created_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        """)
        
        # Tabela de equipamentos
        conn.execute("""
            CREATE TABLE IF NOT EXISTS equipments (
                id INTEGER PRIMARY KEY,
                payload TEXT NOT NULL,  -- JSON serializado
                updated_at TEXT,        -- Data de atualização do registro
                fetched_at INTEGER NOT NULL,  -- Timestamp da busca
                created_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        """)
        
        # Tabela de responsáveis técnicos
        conn.execute("""
            CREATE TABLE IF NOT EXISTS technicians (
                id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,  -- JSON serializado
                updated_at TEXT,        -- Data de atualização do registro
                fetched_at INTEGER NOT NULL,  -- Timestamp da busca
                created_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        """)
        
        # Tabela de estado de sincronização
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sync_state (
                resource TEXT PRIMARY KEY,     -- Nome do recurso (orders, equipments, etc)
                last_updated_at TEXT,          -- Última data de atualização processada
                last_id INTEGER,               -- Último ID processado (fallback se não há timestamp)
                last_full_sync TEXT,           -- Data da última sincronização completa
                total_records INTEGER DEFAULT 0,  -- Total de registros
                sync_type TEXT DEFAULT 'unknown',  -- Tipo do último sync (backfill, incremental)
                synced_at TEXT,                -- Quando foi feito o último sync
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                updated_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        """)
        
        # Criar índices para performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_updated_at ON orders(updated_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_fetched_at ON orders(fetched_at)")
        
        conn.execute("CREATE INDEX IF NOT EXISTS idx_equipments_updated_at ON equipments(updated_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_equipments_fetched_at ON equipments(fetched_at)")
        
        conn.execute("CREATE INDEX IF NOT EXISTS idx_technicians_updated_at ON technicians(updated_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_technicians_fetched_at ON technicians(fetched_at)")
        
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sync_state_resource ON sync_state(resource)")
        
        conn.commit()
        print("✅ Banco de dados inicializado com sucesso")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao inicializar banco de dados: {e}")
        raise


def get_database_info() -> dict:
    """
    Retorna informações sobre o banco de dados.
    """
    conn = get_conn()
    
    try:
        # Verificar se o arquivo existe
        db_exists = DB_PATH.exists()
        db_size = DB_PATH.stat().st_size if db_exists else 0
        
        # Contar registros em cada tabela
        tables_info = {}
        tables = ['orders', 'equipments', 'technicians', 'sync_state']
        
        for table in tables:
            try:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                tables_info[table] = count
            except sqlite3.OperationalError:
                tables_info[table] = "Tabela não existe"
        
        return {
            "database_path": str(DB_PATH),
            "database_exists": db_exists,
            "database_size_bytes": db_size,
            "database_size_mb": round(db_size / (1024 * 1024), 2),
            "tables": tables_info
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "database_path": str(DB_PATH)
        }


def execute_query(query: str, params: Optional[tuple] = None) -> list[sqlite3.Row]:
    """
    Executa uma query SELECT e retorna os resultados.
    
    Args:
        query: Query SQL para executar
        params: Parâmetros para a query (opcional)
    
    Returns:
        Lista de registros como sqlite3.Row
    """
    conn = get_conn()
    cursor = conn.execute(query, params or ())
    return cursor.fetchall()


def execute_update(query: str, params: Optional[tuple] = None) -> int:
    """
    Executa uma query de modificação (INSERT, UPDATE, DELETE).
    
    Args:
        query: Query SQL para executar
        params: Parâmetros para a query (opcional)
    
    Returns:
        Número de linhas afetadas
    """
    conn = get_conn()
    try:
        cursor = conn.execute(query, params or ())
        conn.commit()
        return cursor.rowcount
    except Exception:
        conn.rollback()
        raise


def close_connection() -> None:
    """
    Fecha a conexão com o banco de dados.
    Útil para cleanup em testes ou shutdown da aplicação.
    """
    if 'get_conn' in st.session_state:
        try:
            conn = st.session_state['get_conn']
            conn.close()
            del st.session_state['get_conn']
            print("🔒 Conexão com banco fechada")
        except Exception as e:
            print(f"⚠️ Erro ao fechar conexão: {e}")
