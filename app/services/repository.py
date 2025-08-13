"""
Data Access Layer (DAL) para operações com banco SQLite.

Este módulo fornece funções genéricas para leitura e escrita de dados
no banco SQLite, retornando DataFrames pandas para integração com a aplicação.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd

from ..core.db import execute_query, execute_update, get_conn


class Repository:
    """
    Repositório genérico para operações CRUD com SQLite.
    """
    
    @staticmethod
    def get_orders(
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        estados: Optional[List[int]] = None,
        limit: Optional[int] = None,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Busca ordens de serviço do banco local.
        
        Args:
            date_from: Data início (YYYY-MM-DD)
            date_to: Data fim (YYYY-MM-DD)
            estados: Lista de estados para filtrar
            limit: Limite de registros
            use_cache: Se deve usar cache local (evita reprocessar JSON)
        
        Returns:
            DataFrame com ordens de serviço
        """
        query = "SELECT * FROM orders WHERE 1=1"
        params = []
        
        # Aplicar filtros de data
        if date_from:
            query += " AND updated_at >= ?"
            params.append(date_from)
        
        if date_to:
            query += " AND updated_at <= ?"
            params.append(date_to)
        
        # Ordenar por data mais recente
        query += " ORDER BY updated_at DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            rows = execute_query(query, tuple(params))
            
            if not rows:
                return pd.DataFrame()
            
            # Converter para DataFrame
            data = []
            for row in rows:
                try:
                    # Parse do JSON payload
                    payload = json.loads(row['payload'])
                    
                    # Aplicar filtro de estados se especificado
                    if estados and payload.get('ordem_servico', {}).get('estado') not in estados:
                        continue
                    
                    # Adicionar metadados do banco
                    payload['_db_id'] = row['id']
                    payload['_db_fetched_at'] = row['fetched_at']
                    payload['_db_updated_at'] = row['updated_at']
                    
                    data.append(payload)
                    
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"⚠️ Erro ao processar registro {row['id']}: {e}")
                    continue
            
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            print(f"📊 Carregados {len(df)} registros de ordens do banco local")
            return df
            
        except Exception as e:
            print(f"❌ Erro ao buscar ordens do banco: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_equipments(
        company_id: Optional[int] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Busca equipamentos do banco local.
        
        Args:
            company_id: ID da empresa para filtrar
            limit: Limite de registros
        
        Returns:
            DataFrame com equipamentos
        """
        query = "SELECT * FROM equipments WHERE 1=1"
        params = []
        
        # Ordenar por data mais recente
        query += " ORDER BY updated_at DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            rows = execute_query(query, tuple(params))
            
            if not rows:
                return pd.DataFrame()
            
            # Converter para DataFrame
            data = []
            for row in rows:
                try:
                    # Parse do JSON payload
                    payload = json.loads(row['payload'])
                    
                    # Aplicar filtro de company_id se especificado
                    if company_id and payload.get('proprietario') != company_id:
                        continue
                    
                    # Adicionar metadados do banco
                    payload['_db_id'] = row['id']
                    payload['_db_fetched_at'] = row['fetched_at']
                    payload['_db_updated_at'] = row['updated_at']
                    
                    data.append(payload)
                    
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"⚠️ Erro ao processar equipamento {row['id']}: {e}")
                    continue
            
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            print(f"📊 Carregados {len(df)} equipamentos do banco local")
            return df
            
        except Exception as e:
            print(f"❌ Erro ao buscar equipamentos do banco: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_technicians(limit: Optional[int] = None) -> pd.DataFrame:
        """
        Busca responsáveis técnicos do banco local.
        
        Args:
            limit: Limite de registros
        
        Returns:
            DataFrame com técnicos
        """
        query = "SELECT * FROM technicians ORDER BY updated_at DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            rows = execute_query(query)
            
            if not rows:
                return pd.DataFrame()
            
            # Converter para DataFrame
            data = []
            for row in rows:
                try:
                    # Parse do JSON payload
                    payload = json.loads(row['payload'])
                    
                    # Adicionar metadados do banco
                    payload['_db_id'] = row['id']
                    payload['_db_fetched_at'] = row['fetched_at']
                    payload['_db_updated_at'] = row['updated_at']
                    
                    data.append(payload)
                    
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"⚠️ Erro ao processar técnico {row['id']}: {e}")
                    continue
            
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            print(f"📊 Carregados {len(df)} técnicos do banco local")
            return df
            
        except Exception as e:
            print(f"❌ Erro ao buscar técnicos do banco: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def save_orders(orders_data: List[Dict[str, Any]], batch_size: int = 1000) -> int:
        """
        Salva ordens de serviço no banco local em lotes.
        
        Args:
            orders_data: Lista de dicionários com dados das ordens
            batch_size: Tamanho do lote para inserção
        
        Returns:
            Número de registros salvos
        """
        if not orders_data:
            return 0
        
        conn = get_conn()
        saved_count = 0
        current_time = int(time.time())
        
        try:
            for i in range(0, len(orders_data), batch_size):
                batch = orders_data[i:i + batch_size]
                
                for order in batch:
                    try:
                        order_id = order.get('id')
                        if not order_id:
                            continue
                        
                        # Serializar payload
                        payload = json.dumps(order, ensure_ascii=False)
                        updated_at = order.get('data_criacao') or order.get('updated_at')
                        
                        # Usar REPLACE para atualizar ou inserir
                        conn.execute("""
                            REPLACE INTO orders (id, payload, updated_at, fetched_at)
                            VALUES (?, ?, ?, ?)
                        """, (order_id, payload, updated_at, current_time))
                        
                        saved_count += 1
                        
                    except Exception as e:
                        print(f"⚠️ Erro ao salvar ordem {order.get('id', 'unknown')}: {e}")
                        continue
                
                # Commit a cada lote
                conn.commit()
            
            print(f"✅ Salvadas {saved_count} ordens no banco local")
            return saved_count
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Erro ao salvar ordens: {e}")
            return saved_count
    
    @staticmethod
    def save_equipments(equipments_data: List[Dict[str, Any]], batch_size: int = 1000) -> int:
        """
        Salva equipamentos no banco local em lotes.
        
        Args:
            equipments_data: Lista de dicionários com dados dos equipamentos
            batch_size: Tamanho do lote para inserção
        
        Returns:
            Número de registros salvos
        """
        if not equipments_data:
            return 0
        
        conn = get_conn()
        saved_count = 0
        current_time = int(time.time())
        
        try:
            for i in range(0, len(equipments_data), batch_size):
                batch = equipments_data[i:i + batch_size]
                
                for equipment in batch:
                    try:
                        equipment_id = equipment.get('id')
                        if not equipment_id:
                            continue
                        
                        # Serializar payload
                        payload = json.dumps(equipment, ensure_ascii=False)
                        updated_at = equipment.get('updated_at')
                        
                        # Usar REPLACE para atualizar ou inserir
                        conn.execute("""
                            REPLACE INTO equipments (id, payload, updated_at, fetched_at)
                            VALUES (?, ?, ?, ?)
                        """, (equipment_id, payload, updated_at, current_time))
                        
                        saved_count += 1
                        
                    except Exception as e:
                        print(f"⚠️ Erro ao salvar equipamento {equipment.get('id', 'unknown')}: {e}")
                        continue
                
                # Commit a cada lote
                conn.commit()
            
            print(f"✅ Salvados {saved_count} equipamentos no banco local")
            return saved_count
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Erro ao salvar equipamentos: {e}")
            return saved_count
    
    @staticmethod
    def update_sync_state(
        resource: str,
        last_updated_at: Optional[str] = None,
        total_records: Optional[int] = None
    ) -> None:
        """
        Atualiza estado de sincronização de um recurso.
        
        Args:
            resource: Nome do recurso (orders, equipments, etc)
            last_updated_at: Data da última atualização
            total_records: Total de registros sincronizados
        """
        current_time = int(time.time())
        current_date = datetime.now().isoformat()
        
        try:
            # Verificar se já existe
            existing = execute_query(
                "SELECT * FROM sync_state WHERE resource = ?",
                (resource,)
            )
            
            if existing:
                # Atualizar registro existente
                execute_update("""
                    UPDATE sync_state 
                    SET last_updated_at = COALESCE(?, last_updated_at),
                        total_records = COALESCE(?, total_records),
                        last_full_sync = ?,
                        updated_at = ?
                    WHERE resource = ?
                """, (last_updated_at, total_records, current_date, current_time, resource))
            else:
                # Criar novo registro
                execute_update("""
                    INSERT INTO sync_state (resource, last_updated_at, total_records, last_full_sync, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (resource, last_updated_at, total_records or 0, current_date, current_time))
            
            print(f"✅ Estado de sincronização atualizado para {resource}")
            
        except Exception as e:
            print(f"❌ Erro ao atualizar sync_state para {resource}: {e}")
    
    @staticmethod
    def get_sync_state(resource: str) -> Optional[Dict[str, Any]]:
        """
        Recupera estado de sincronização de um recurso.
        
        Args:
            resource: Nome do recurso
        
        Returns:
            Dicionário com estado ou None se não encontrado
        """
        try:
            rows = execute_query(
                "SELECT * FROM sync_state WHERE resource = ?",
                (resource,)
            )
            
            if rows:
                row = rows[0]
                return {
                    'resource': row['resource'],
                    'last_updated_at': row['last_updated_at'],
                    'last_full_sync': row['last_full_sync'],
                    'total_records': row['total_records'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
            
            return None
            
        except Exception as e:
            print(f"❌ Erro ao buscar sync_state para {resource}: {e}")
            return None
    
    @staticmethod
    def is_data_fresh(resource: str, max_age_hours: int = 1) -> bool:
        """
        Verifica se os dados locais estão atualizados.
        
        Args:
            resource: Nome do recurso
            max_age_hours: Idade máxima em horas para considerar dados frescos
        
        Returns:
            True se dados estão frescos, False caso contrário
        """
        sync_state = Repository.get_sync_state(resource)
        
        if not sync_state or not sync_state.get('last_full_sync'):
            return False
        
        try:
            last_sync = datetime.fromisoformat(sync_state['last_full_sync'])
            max_age = timedelta(hours=max_age_hours)
            
            return (datetime.now() - last_sync) < max_age
            
        except Exception:
            return False
    
    @staticmethod
    def clear_old_data(resource: str, keep_days: int = 30) -> int:
        """
        Remove dados antigos do banco para economizar espaço.
        
        Args:
            resource: Nome do recurso (orders, equipments, etc)
            keep_days: Número de dias para manter os dados
        
        Returns:
            Número de registros removidos
        """
        cutoff_date = (datetime.now() - timedelta(days=keep_days)).isoformat()
        
        try:
            table_map = {
                'orders': 'orders',
                'equipments': 'equipments',
                'technicians': 'technicians'
            }
            
            table_name = table_map.get(resource)
            if not table_name:
                print(f"⚠️ Recurso desconhecido: {resource}")
                return 0
            
            deleted = execute_update(
                f"DELETE FROM {table_name} WHERE updated_at < ?",
                (cutoff_date,)
            )
            
            print(f"🗑️ Removidos {deleted} registros antigos de {resource}")
            return deleted
            
        except Exception as e:
            print(f"❌ Erro ao limpar dados antigos de {resource}: {e}")
            return 0


# Instância global do repositório
repository = Repository()
