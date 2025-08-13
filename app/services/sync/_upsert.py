"""
Módulo para operações de upsert idempotente e controle de rate limiting.
"""
import json
import time
import asyncio
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
import streamlit as st
from app.core.logging import app_logger


class RateLimiter:
    """Controla rate limiting com backoff exponencial."""
    
    def __init__(self, base_delay: float = 0.1, max_delay: float = 10.0, backoff_factor: float = 2.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.current_delay = base_delay
        self.error_count = 0
    
    async def wait(self):
        """Espera o tempo atual de delay."""
        if self.current_delay > 0:
            await asyncio.sleep(self.current_delay)
    
    def on_success(self):
        """Reseta delay após sucesso."""
        self.current_delay = self.base_delay
        self.error_count = 0
    
    def on_error(self):
        """Aumenta delay após erro."""
        self.error_count += 1
        self.current_delay = min(
            self.current_delay * self.backoff_factor,
            self.max_delay
        )
        app_logger.warning(f"Rate limit hit, increasing delay to {self.current_delay:.2f}s")


def upsert_records(
    conn: sqlite3.Connection, 
    table: str, 
    records: List[Dict[str, Any]],
    progress_callback: Optional[callable] = None
) -> int:
    """
    Executa upsert idempotente de registros no banco.
    
    Args:
        conn: Conexão SQLite
        table: Nome da tabela de destino ('orders', 'equipments', 'technicians')
        records: Lista de registros para inserir/atualizar
        progress_callback: Função callback para progresso (opcional)
    
    Returns:
        int: Número de registros processados
    """
    if not records:
        return 0
    
    try:
        current_timestamp = int(time.time())
        
        # SQL de upsert usando formato payload
        sql = f"""
            INSERT OR REPLACE INTO {table} (id, payload, updated_at, fetched_at) 
            VALUES (?, ?, ?, ?)
        """
        
        # Preparar dados para insert
        batch_data = []
        
        for record in records:
            record_id = record.get('id')
            if not record_id:
                continue  # Pular registros sem ID
                
            # Serializar registro completo como JSON
            payload = json.dumps(record, ensure_ascii=False, default=str)
            updated_at = record.get('updated_at')
            
            batch_data.append((record_id, payload, updated_at, current_timestamp))
        
        # Executar em lotes para performance
        batch_size = 500
        processed = 0
        
        for i in range(0, len(batch_data), batch_size):
            batch = batch_data[i:i + batch_size]
            
            conn.executemany(sql, batch)
            processed += len(batch)
            
            # Callback de progresso
            if progress_callback:
                progress_callback(processed, len(batch_data))
        
        conn.commit()
        
        app_logger.log_info(f"✅ Upsert completed: {processed:,} records in {table}")
        return processed
    
    except sqlite3.Error as e:
        conn.rollback()
        app_logger.log_error(f"❌ SQLite error during upsert: {e}")
        raise
    
    except Exception as e:
        conn.rollback()
        app_logger.log_error(f"❌ Unexpected error during upsert: {e}")
        raise


def update_sync_state(
    conn: sqlite3.Connection,
    resource: str,
    last_updated_at: Optional[str] = None,
    last_id: Optional[int] = None,
    total_records: Optional[int] = None,
    sync_type: str = 'unknown'
) -> None:
    """
    Atualiza estado de sincronização após operação bem-sucedida.
    
    Args:
        conn: Conexão SQLite
        resource: Nome do recurso (ex: 'orders', 'equipments')
        last_updated_at: Último timestamp processado
        last_id: Último ID processado (fallback se não há timestamp)
        total_records: Total de registros processados
        sync_type: Tipo de sync ('backfill', 'incremental')
    """
    try:
        current_time = datetime.now().isoformat()
        
        sql = """
            INSERT OR REPLACE INTO sync_state (
                resource, last_updated_at, last_id, total_records, 
                sync_type, synced_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """
        
        conn.execute(sql, (
            resource,
            last_updated_at,
            last_id,
            total_records,
            sync_type,
            current_time
        ))
        conn.commit()
        
        app_logger.log_info(f"✅ Sync state updated for {resource}: type={sync_type}, records={total_records}")
    
    except sqlite3.Error as e:
        app_logger.log_error(f"❌ Error updating sync state: {e}")
        raise


def get_last_sync_info(conn: sqlite3.Connection, resource: str) -> Optional[Dict[str, Any]]:
    """
    Obtém informações do último sync para um recurso.
    
    Args:
        conn: Conexão SQLite
        resource: Nome do recurso
    
    Returns:
        Dict com informações do sync ou None se não encontrado
    """
    try:
        sql = """
            SELECT resource, last_updated_at, last_id, total_records, 
                   sync_type, synced_at 
            FROM sync_state 
            WHERE resource = ?
            ORDER BY synced_at DESC 
            LIMIT 1
        """
        
        cursor = conn.execute(sql, (resource,))
        row = cursor.fetchone()
        
        if row:
            return {
                'resource': row[0],
                'last_updated_at': row[1],
                'last_id': row[2],
                'total_records': row[3],
                'sync_type': row[4],
                'synced_at': row[5]
            }
        
        return None
    
    except sqlite3.Error as e:
        app_logger.log_error(f"❌ Error getting last sync info: {e}")
        return None


class ProgressTracker:
    """Rastreia progresso de operações de sincronização."""
    
    def __init__(self, total: int, description: str = "Sincronizando"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()
        
        # Para Streamlit UI
        if hasattr(st, 'empty'):
            self.progress_bar = st.progress(0)
            self.status_text = st.empty()
    
    def update(self, current: int, total: Optional[int] = None):
        """Atualiza progresso."""
        if total:
            self.total = total
        self.current = current
        
        if self.total > 0:
            percent = min(100, int((current / self.total) * 100))
            elapsed = time.time() - self.start_time
            
            # Estimativa de tempo restante
            if current > 0:
                eta = (elapsed / current) * (self.total - current)
                eta_str = f" (ETA: {eta:.0f}s)"
            else:
                eta_str = ""
            
            message = f"{self.description}: {current:,}/{self.total:,} ({percent}%){eta_str}"
            
            # Update Streamlit UI se disponível
            if hasattr(self, 'progress_bar'):
                self.progress_bar.progress(percent / 100)
                self.status_text.text(message)
            
            app_logger.log_info(f"📊 {message}")
    
    def complete(self):
        """Marca como completo."""
        elapsed = time.time() - self.start_time
        message = f"✅ {self.description} completo: {self.current:,} registros em {elapsed:.1f}s"
        
        if hasattr(self, 'progress_bar'):
            self.progress_bar.progress(1.0)
            self.status_text.text(message)
        
        app_logger.log_info(message)
