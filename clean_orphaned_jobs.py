#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.abspath("."))

from app.core.db import get_conn

print("🧹 Limpando jobs órfãos...")

with get_conn() as conn:
    cursor = conn.execute("UPDATE sync_jobs SET status = 'error' WHERE status = 'running'")
    print(f"✅ Jobs órfãos limpos: {cursor.rowcount}")
    
    cursor = conn.execute("SELECT COUNT(*) FROM sync_jobs WHERE status = 'running'")
    remaining = cursor.fetchone()[0]
    print(f"📊 Jobs restantes em execução: {remaining}")
    
if remaining == 0:
    print("🎉 Sincronização automática pode funcionar agora!")
else:
    print("⚠️ Ainda há jobs em execução")
