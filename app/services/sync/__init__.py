"""
Sistema de sincronização incremental para otimizar cache de dados.

Este módulo implementa:
- Backfill completo (primeira sincronização)
- Sincronização incremental baseada em timestamps
- Upsert idempotente com controle de duplicatas
- Rate limiting e retry logic
"""
from .ingest import BackfillSync
from .delta import IncrementalSync
from ._upsert import upsert_records, RateLimiter

__all__ = [
    'BackfillSync',
    'IncrementalSync', 
    'upsert_records',
    'RateLimiter'
]
