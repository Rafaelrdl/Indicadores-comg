"""
Sistema de backfill completo para sincronização inicial de dados.
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import streamlit as st

from app.arkmeds_client.client import ArkmedsClient
from app.core.db import get_conn
from app.core.logging import app_logger as logger
from ._upsert import upsert_records, update_sync_state, RateLimiter, ProgressTracker


class BackfillSync:
    """Gerencia sincronização completa (backfill) de dados da API."""
    
    def __init__(self, client: ArkmedsClient):
        self.client = client
        self.rate_limiter = RateLimiter()
    
    async def sync_orders(
        self, 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        **filters
    ) -> int:
        """
        Sincroniza todas as ordens de serviço.
        
        Args:
            start_date: Data inicial (opcional)
            end_date: Data final (opcional) 
            **filters: Filtros adicionais
        
        Returns:
            int: Número total de registros sincronizados
        """
        logger.log_info("🔄 Iniciando backfill de ordens de serviço...")
        
        try:
            # Preparar filtros
            api_filters = dict(filters)
            if start_date:
                api_filters['data_criacao__gte'] = start_date
            if end_date:
                api_filters['data_criacao__lte'] = end_date
            
            # Buscar todos os dados com paginação
            all_orders = await self._fetch_all_paginated('chamados', api_filters)
            
            if not all_orders:
                logger.log_info("📋 Nenhuma ordem encontrada para sincronizar")
                return 0
            
            # Preparar para upsert
            conn = get_conn()
            progress = ProgressTracker(len(all_orders), "Salvando ordens")
            
            def progress_callback(current, total):
                progress.update(current, total)
            
            # Converter para formato do banco
            records = []
            for order in all_orders:
                record = order.model_dump() if hasattr(order, 'model_dump') else order
                records.append(record)
            
            # Fazer upsert
            processed = upsert_records(conn, 'orders', records, progress_callback)
            
            # Atualizar estado de sync
            last_updated = None
            last_id = None
            
            if records:
                # Tentar usar updated_at se disponível, senão usar ID
                last_record = max(records, key=lambda r: r.get('id', 0))
                last_updated = last_record.get('updated_at') 
                last_id = last_record.get('id')
            
            update_sync_state(
                conn, 'orders', 
                last_updated_at=last_updated,
                last_id=last_id,
                total_records=processed,
                sync_type='backfill'
            )
            
            progress.complete()
            return processed
        
        except Exception as e:
            logger.log_error(f"❌ Erro durante backfill de ordens: {e}")
            raise
    
    async def sync_equipments(self, **filters) -> int:
        """
        Sincroniza todos os equipamentos.
        
        Args:
            **filters: Filtros adicionais
        
        Returns:
            int: Número total de registros sincronizados
        """
        logger.log_info("🔄 Iniciando backfill de equipamentos...")
        
        try:
            # Buscar todos os equipamentos
            all_equipments = await self._fetch_all_paginated('equipments', filters)
            
            if not all_equipments:
                logger.log_info("🔧 Nenhum equipamento encontrado para sincronizar")
                return 0
            
            # Preparar para upsert
            conn = get_conn()
            progress = ProgressTracker(len(all_equipments), "Salvando equipamentos")
            
            def progress_callback(current, total):
                progress.update(current, total)
            
            # Converter para formato do banco
            records = []
            for equip in all_equipments:
                record = equip.model_dump() if hasattr(equip, 'model_dump') else equip
                records.append(record)
            
            # Fazer upsert
            processed = upsert_records(conn, 'equipments', records, progress_callback)
            
            # Atualizar estado de sync
            last_updated = None
            last_id = None
            
            if records:
                last_record = max(records, key=lambda r: r.get('id', 0))
                last_updated = last_record.get('updated_at')
                last_id = last_record.get('id')
            
            update_sync_state(
                conn, 'equipments',
                last_updated_at=last_updated,
                last_id=last_id,
                total_records=processed,
                sync_type='backfill'
            )
            
            progress.complete()
            return processed
        
        except Exception as e:
            logger.log_error(f"❌ Erro durante backfill de equipamentos: {e}")
            raise
    
    async def sync_technicians(self, **filters) -> int:
        """
        Sincroniza todos os técnicos.
        
        Args:
            **filters: Filtros adicionais
        
        Returns:
            int: Número total de registros sincronizados
        """
        logger.log_info("🔄 Iniciando backfill de técnicos...")
        
        try:
            # Buscar todos os técnicos
            all_technicians = await self._fetch_all_paginated('technicians', filters)
            
            if not all_technicians:
                logger.log_info("👥 Nenhum técnico encontrado para sincronizar")
                return 0
            
            # Preparar para upsert
            conn = get_conn()
            progress = ProgressTracker(len(all_technicians), "Salvando técnicos")
            
            def progress_callback(current, total):
                progress.update(current, total)
            
            # Converter para formato do banco
            records = []
            for tech in all_technicians:
                record = tech.model_dump() if hasattr(tech, 'model_dump') else tech
                records.append(record)
            
            # Fazer upsert
            processed = upsert_records(conn, 'technicians', records, progress_callback)
            
            # Atualizar estado de sync
            last_updated = None
            last_id = None
            
            if records:
                last_record = max(records, key=lambda r: r.get('id', 0))
                last_updated = last_record.get('updated_at')
                last_id = last_record.get('id')
            
            update_sync_state(
                conn, 'technicians',
                last_updated_at=last_updated,
                last_id=last_id,
                total_records=processed,
                sync_type='backfill'
            )
            
            progress.complete()
            return processed
        
        except Exception as e:
            logger.log_error(f"❌ Erro durante backfill de técnicos: {e}")
            raise
    
    async def sync_all(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        **filters
    ) -> Dict[str, int]:
        """
        Sincroniza todos os recursos em sequência.
        
        Args:
            start_date: Data inicial para ordens (opcional)
            end_date: Data final para ordens (opcional)
            **filters: Filtros adicionais
        
        Returns:
            Dict com contadores por recurso
        """
        logger.log_info("🚀 Iniciando backfill completo de todos os recursos...")
        
        results = {}
        
        try:
            # Sincronizar em sequência para não sobrecarregar a API
            results['orders'] = await self.sync_orders(start_date, end_date, **filters)
            await asyncio.sleep(2)  # Pausa entre recursos
            
            results['equipments'] = await self.sync_equipments(**filters)
            await asyncio.sleep(2)
            
            results['technicians'] = await self.sync_technicians(**filters)
            
            total = sum(results.values())
            logger.log_info(f"🎉 Backfill completo! Total: {total:,} registros sincronizados")
            
            return results
        
        except Exception as e:
            logger.log_error(f"❌ Erro durante backfill completo: {e}")
            raise
    
    async def _fetch_all_paginated(
        self, 
        resource_type: str, 
        filters: Dict[str, Any]
    ) -> List[Any]:
        """
        Busca todos os registros de um recurso usando paginação.
        
        Args:
            resource_type: Tipo do recurso ('chamados', 'equipments', etc)
            filters: Filtros para a busca
        
        Returns:
            Lista com todos os registros
        """
        all_records = []
        
        try:
            # Mapeamento de tipos para métodos do client
            method_map = {
                'chamados': self.client.list_chamados,
                'orders': self.client.list_chamados,
                'equipments': getattr(self.client, 'list_equipments', None),
                'technicians': getattr(self.client, 'list_technicians', None)
            }
            
            fetch_method = method_map.get(resource_type)
            if not fetch_method:
                logger.log_warning(f"⚠️ Método não encontrado para {resource_type}")
                return []
            
            # Para ordens, usar o método existente que já tem paginação
            if resource_type in ['chamados', 'orders']:
                records = await fetch_method(filters)
                return records
            
            # Para outros recursos, implementar paginação se necessário
            else:
                # Por enquanto, buscar diretamente
                # TODO: Implementar paginação para outros recursos se a API suportar
                if hasattr(fetch_method, '__call__'):
                    records = await fetch_method(filters)
                    return records if isinstance(records, list) else []
        
        except Exception as e:
            logger.log_error(f"❌ Erro buscando {resource_type}: {e}")
            await self.rate_limiter.wait()
            self.rate_limiter.on_error()
            raise
        
        return all_records


# Função de conveniência para uso direto
async def run_backfill(
    client: ArkmedsClient,
    resources: List[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    **filters
) -> Dict[str, int]:
    """
    Executa backfill para recursos especificados.
    
    Args:
        client: Cliente da API
        resources: Lista de recursos ('orders', 'equipments', 'technicians')
        start_date: Data inicial (apenas para orders)
        end_date: Data final (apenas para orders)
        **filters: Filtros adicionais
    
    Returns:
        Dict com resultados por recurso
    """
    if resources is None:
        resources = ['orders', 'equipments', 'technicians']
    
    sync = BackfillSync(client)
    results = {}
    
    for resource in resources:
        try:
            if resource == 'orders':
                results[resource] = await sync.sync_orders(start_date, end_date, **filters)
            elif resource == 'equipments':
                results[resource] = await sync.sync_equipments(**filters)
            elif resource == 'technicians':
                results[resource] = await sync.sync_technicians(**filters)
            else:
                logger.log_warning(f"⚠️ Recurso desconhecido: {resource}")
            
            # Pausa entre recursos
            await asyncio.sleep(1)
        
        except Exception as e:
            logger.log_error(f"❌ Falha no backfill de {resource}: {e}")
            results[resource] = 0
    
    return results
