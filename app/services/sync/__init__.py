"""
Sistema de sincronização incremental para otimizar cache de dados.

Este módulo implementa:
- Backfill completo (primeira sincronização)
- Sincronização incremental baseada em timestamps
- Upsert idempotente com controle de duplicatas
- Rate limiting e retry logic
"""
from ._upsert import RateLimiter, upsert_records
from .delta import IncrementalSync
from .ingest import BackfillSync


__all__ = [
    'BackfillSync',
    'IncrementalSync',
    'RateLimiter',
    'upsert_records'
]
