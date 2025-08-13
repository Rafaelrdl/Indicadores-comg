"""
Sistema de sincronização incremental (delta) baseado em timestamps.
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import streamlit as st

from app.arkmeds_client.client import ArkmedsClient
from app.core.db import get_conn
from app.core.logging import app_logger as logger
from ._upsert import (
    upsert_records, 
    update_sync_state, 
    get_last_sync_info,
    RateLimiter, 
    ProgressTracker
)


class IncrementalSync:
    """Gerencia sincronização incremental de dados baseada em timestamps."""
    
    def __init__(self, client: ArkmedsClient):
        self.client = client
        self.rate_limiter = RateLimiter()
    
    async def sync_orders_incremental(self, **filters) -> int:
        """
        Sincroniza apenas ordens novas/modificadas desde último sync.
        
        Args:
            **filters: Filtros adicionais
        
        Returns:
            int: Número de registros sincronizados
        """
        logger.info("🔄 Iniciando sincronização incremental de ordens...")
        
        try:
            conn = get_conn()
            
            # Obter informações do último sync
            last_sync = get_last_sync_info(conn, 'orders')
            
            # Determinar ponto de partida para delta
            delta_filters = dict(filters)
            
            if last_sync and last_sync.get('last_updated_at'):
                # Usar timestamp se disponível
                delta_filters['updated_at__gt'] = last_sync['last_updated_at']
                logger.info(f"📅 Buscando ordens atualizadas após {last_sync['last_updated_at']}")
            
            elif last_sync and last_sync.get('last_id'):
                # Fallback para ID se não há timestamp
                delta_filters['id__gt'] = last_sync['last_id']
                logger.info(f"🔢 Buscando ordens com ID > {last_sync['last_id']}")
            
            else:
                # Primeira sincronização - buscar apenas últimas 24h para não sobrecarregar
                from datetime import timedelta
                yesterday = datetime.now() - timedelta(days=1)
                delta_filters['data_criacao__gte'] = yesterday.date()
                logger.info("🆕 Primeira sincronização - buscando últimas 24h")
            
            # Buscar dados incrementais
            new_orders = await self._fetch_incremental_data('chamados', delta_filters)
            
            if not new_orders:
                logger.info("📋 Nenhuma ordem nova para sincronizar")
                return 0
            
            logger.info(f"📋 Encontradas {len(new_orders):,} ordens para sincronizar")
            
            # Preparar progresso
            progress = ProgressTracker(len(new_orders), "Sincronizando ordens")
            
            def progress_callback(current, total):
                progress.update(current, total)
            
            # Converter para formato do banco
            records = []
            for order in new_orders:
                record = order.model_dump() if hasattr(order, 'model_dump') else order
                records.append(record)
            
            # Fazer upsert
            processed = upsert_records(conn, 'orders', records, progress_callback)
            
            # Atualizar estado de sync
            if records:
                # Encontrar último registro por timestamp ou ID
                if any(r.get('updated_at') for r in records):
                    last_record = max(
                        (r for r in records if r.get('updated_at')), 
                        key=lambda r: r['updated_at']
                    )
                    last_updated = last_record.get('updated_at')
                    last_id = last_record.get('id')
                else:
                    last_record = max(records, key=lambda r: r.get('id', 0))
                    last_updated = None
                    last_id = last_record.get('id')
                
                # Somar com total anterior se houver
                total_records = processed
                if last_sync and last_sync.get('total_records'):
                    total_records += last_sync['total_records']
                
                update_sync_state(
                    conn, 'orders',
                    last_updated_at=last_updated,
                    last_id=last_id,
                    total_records=total_records,
                    sync_type='incremental'
                )
            
            progress.complete()
            return processed
        
        except Exception as e:
            logger.error(f"❌ Erro durante sync incremental de ordens: {e}")
            raise
    
    async def sync_equipments_incremental(self, **filters) -> int:
        """
        Sincroniza apenas equipamentos novos/modificados.
        
        Args:
            **filters: Filtros adicionais
        
        Returns:
            int: Número de registros sincronizados
        """
        logger.info("🔄 Iniciando sincronização incremental de equipamentos...")
        
        try:
            conn = get_conn()
            last_sync = get_last_sync_info(conn, 'equipments')
            
            # Determinar filtros incrementais
            delta_filters = dict(filters)
            
            if last_sync and last_sync.get('last_updated_at'):
                delta_filters['updated_at__gt'] = last_sync['last_updated_at']
                logger.info(f"📅 Buscando equipamentos atualizados após {last_sync['last_updated_at']}")
            
            elif last_sync and last_sync.get('last_id'):
                delta_filters['id__gt'] = last_sync['last_id']
                logger.info(f"🔢 Buscando equipamentos com ID > {last_sync['last_id']}")
            
            else:
                logger.info("🆕 Primeira sincronização de equipamentos")
            
            # Buscar dados incrementais
            new_equipments = await self._fetch_incremental_data('equipments', delta_filters)
            
            if not new_equipments:
                logger.info("🔧 Nenhum equipamento novo para sincronizar")
                return 0
            
            logger.info(f"🔧 Encontrados {len(new_equipments):,} equipamentos para sincronizar")
            
            # Processar sincronização
            progress = ProgressTracker(len(new_equipments), "Sincronizando equipamentos")
            
            def progress_callback(current, total):
                progress.update(current, total)
            
            records = []
            for equip in new_equipments:
                record = equip.model_dump() if hasattr(equip, 'model_dump') else equip
                records.append(record)
            
            processed = upsert_records(conn, 'equipments', records, progress_callback)
            
            # Atualizar sync state
            if records:
                if any(r.get('updated_at') for r in records):
                    last_record = max(
                        (r for r in records if r.get('updated_at')), 
                        key=lambda r: r['updated_at']
                    )
                    last_updated = last_record.get('updated_at')
                    last_id = last_record.get('id')
                else:
                    last_record = max(records, key=lambda r: r.get('id', 0))
                    last_updated = None
                    last_id = last_record.get('id')
                
                total_records = processed
                if last_sync and last_sync.get('total_records'):
                    total_records += last_sync['total_records']
                
                update_sync_state(
                    conn, 'equipments',
                    last_updated_at=last_updated,
                    last_id=last_id,
                    total_records=total_records,
                    sync_type='incremental'
                )
            
            progress.complete()
            return processed
        
        except Exception as e:
            logger.error(f"❌ Erro durante sync incremental de equipamentos: {e}")
            raise
    
    async def sync_technicians_incremental(self, **filters) -> int:
        """
        Sincroniza apenas técnicos novos/modificados.
        
        Args:
            **filters: Filtros adicionais
        
        Returns:
            int: Número de registros sincronizados
        """
        logger.info("🔄 Iniciando sincronização incremental de técnicos...")
        
        try:
            conn = get_conn()
            last_sync = get_last_sync_info(conn, 'technicians')
            
            # Determinar filtros incrementais
            delta_filters = dict(filters)
            
            if last_sync and last_sync.get('last_updated_at'):
                delta_filters['updated_at__gt'] = last_sync['last_updated_at']
                logger.info(f"📅 Buscando técnicos atualizados após {last_sync['last_updated_at']}")
            
            elif last_sync and last_sync.get('last_id'):
                delta_filters['id__gt'] = last_sync['last_id']
                logger.info(f"🔢 Buscando técnicos com ID > {last_sync['last_id']}")
            
            else:
                logger.info("🆕 Primeira sincronização de técnicos")
            
            # Buscar dados incrementais
            new_technicians = await self._fetch_incremental_data('technicians', delta_filters)
            
            if not new_technicians:
                logger.info("👥 Nenhum técnico novo para sincronizar")
                return 0
            
            logger.info(f"👥 Encontrados {len(new_technicians):,} técnicos para sincronizar")
            
            # Processar sincronização
            progress = ProgressTracker(len(new_technicians), "Sincronizando técnicos")
            
            def progress_callback(current, total):
                progress.update(current, total)
            
            records = []
            for tech in new_technicians:
                record = tech.model_dump() if hasattr(tech, 'model_dump') else tech
                records.append(record)
            
            processed = upsert_records(conn, 'technicians', records, progress_callback)
            
            # Atualizar sync state
            if records:
                if any(r.get('updated_at') for r in records):
                    last_record = max(
                        (r for r in records if r.get('updated_at')), 
                        key=lambda r: r['updated_at']
                    )
                    last_updated = last_record.get('updated_at')
                    last_id = last_record.get('id')
                else:
                    last_record = max(records, key=lambda r: r.get('id', 0))
                    last_updated = None
                    last_id = last_record.get('id')
                
                total_records = processed
                if last_sync and last_sync.get('total_records'):
                    total_records += last_sync['total_records']
                
                update_sync_state(
                    conn, 'technicians',
                    last_updated_at=last_updated,
                    last_id=last_id,
                    total_records=total_records,
                    sync_type='incremental'
                )
            
            progress.complete()
            return processed
        
        except Exception as e:
            logger.error(f"❌ Erro durante sync incremental de técnicos: {e}")
            raise
    
    async def sync_all_incremental(self, **filters) -> Dict[str, int]:
        """
        Executa sincronização incremental para todos os recursos.
        
        Args:
            **filters: Filtros adicionais
        
        Returns:
            Dict com contadores por recurso
        """
        logger.info("🚀 Iniciando sincronização incremental completa...")
        
        results = {}
        
        try:
            # Sincronizar em sequência para controlar carga na API
            results['orders'] = await self.sync_orders_incremental(**filters)
            await asyncio.sleep(1)  # Pausa entre recursos
            
            results['equipments'] = await self.sync_equipments_incremental(**filters)
            await asyncio.sleep(1)
            
            results['technicians'] = await self.sync_technicians_incremental(**filters)
            
            total = sum(results.values())
            logger.info(f"🎉 Sincronização incremental completa! Total: {total:,} novos registros")
            
            return results
        
        except Exception as e:
            logger.error(f"❌ Erro durante sincronização incremental completa: {e}")
            raise
    
    async def _fetch_incremental_data(
        self, 
        resource_type: str, 
        filters: Dict[str, Any]
    ) -> List[Any]:
        """
        Busca dados incrementais com base nos filtros.
        
        Args:
            resource_type: Tipo do recurso
            filters: Filtros incluindo condições de delta
        
        Returns:
            Lista com registros novos/modificados
        """
        try:
            # Aplicar rate limiting
            await self.rate_limiter.wait()
            
            # Mapeamento de tipos para métodos do client
            method_map = {
                'chamados': self.client.list_chamados,
                'orders': self.client.list_chamados,
                'equipments': getattr(self.client, 'list_equipments', None),
                'technicians': getattr(self.client, 'list_technicians', None)
            }
            
            fetch_method = method_map.get(resource_type)
            if not fetch_method:
                logger.warning(f"⚠️ Método não encontrado para {resource_type}")
                return []
            
            # Buscar dados
            records = await fetch_method(filters)
            
            self.rate_limiter.on_success()
            return records if isinstance(records, list) else []
        
        except Exception as e:
            logger.error(f"❌ Erro buscando dados incrementais de {resource_type}: {e}")
            self.rate_limiter.on_error()
            await self.rate_limiter.wait()
            raise


# Funções de conveniência para uso direto
async def run_incremental_sync(
    client: ArkmedsClient,
    resources: List[str] = None,
    **filters
) -> Dict[str, int]:
    """
    Executa sincronização incremental para recursos especificados.
    
    Args:
        client: Cliente da API
        resources: Lista de recursos ('orders', 'equipments', 'technicians')
        **filters: Filtros adicionais
    
    Returns:
        Dict com resultados por recurso
    """
    if resources is None:
        resources = ['orders', 'equipments', 'technicians']
    
    sync = IncrementalSync(client)
    results = {}
    
    for resource in resources:
        try:
            if resource == 'orders':
                results[resource] = await sync.sync_orders_incremental(**filters)
            elif resource == 'equipments':
                results[resource] = await sync.sync_equipments_incremental(**filters)
            elif resource == 'technicians':
                results[resource] = await sync.sync_technicians_incremental(**filters)
            else:
                logger.warning(f"⚠️ Recurso desconhecido: {resource}")
                results[resource] = 0
            
            # Pausa entre recursos
            await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"❌ Falha na sincronização incremental de {resource}: {e}")
            results[resource] = 0
    
    return results


def should_run_incremental_sync(resource: str, max_age_hours: int = 2) -> bool:
    """
    Verifica se deve executar sincronização incremental baseado na idade dos dados.
    
    Args:
        resource: Nome do recurso
        max_age_hours: Idade máxima em horas antes de sincronizar
    
    Returns:
        bool: True se deve sincronizar
    """
    try:
        conn = get_conn()
        last_sync = get_last_sync_info(conn, resource)
        
        if not last_sync:
            return True  # Nunca sincronizou
        
        # Verificar idade do último sync
        from datetime import datetime, timedelta
        last_sync_time = datetime.fromisoformat(last_sync['synced_at'])
        max_age = timedelta(hours=max_age_hours)
        
        return datetime.now() - last_sync_time > max_age
    
    except Exception as e:
        logger.error(f"❌ Erro verificando necessidade de sync: {e}")
        return True  # Em caso de erro, sincronizar por segurança
