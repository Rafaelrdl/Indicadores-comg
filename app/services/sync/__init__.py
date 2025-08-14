"""
Sistema de sincronização incremental para otimizar cache de dados.

Este módulo implementa:
- Backfill completo (primeira sincronização)
- Sincronização incremental baseada em timestamps e páginas
- Upsert idempotente com controle de duplicatas
- Rate limiting e retry logic
"""

from ._upsert import RateLimiter, upsert_records
from .delta import IncrementalSync, IncrementalSyncWithPages
from .ingest import BackfillSync


__all__ = ["BackfillSync", "IncrementalSync", "IncrementalSyncWithPages", "RateLimiter", "upsert_records"]
