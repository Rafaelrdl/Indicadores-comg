#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.abspath("."))

from app.core.db import get_conn

print("🔍 Verificando jobs no banco de dados:")
print("=" * 60)

try:
    with get_conn() as conn:
        cursor = conn.execute("""
            SELECT job_id, kind, status, last_page_synced, finished_at 
            FROM sync_jobs 
            WHERE kind = ? 
            ORDER BY finished_at DESC
        """, ("delta",))
        
        rows = cursor.fetchall()
        
        if not rows:
            print("❌ Nenhum job encontrado")
        else:
            print(f"📋 Encontrados {len(rows)} jobs:")
            for row in rows:
                print(f"   {row[0]}: {row[2]} - página {row[3]} - {row[4]}")
                
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
