#!/usr/bin/env python3
"""Script para limpar jobs orfãos de sincronização."""

from app.core.db import get_conn
from app.services.sync_jobs import get_running_job
from datetime import datetime, timedelta

def clean_orphaned_jobs():
    print("=== LIMPANDO JOBS ORFÃOS ===")
    
    with get_conn() as conn:
        # Buscar jobs "running" antigos (mais de 1 hora)
        cursor = conn.execute("""
            SELECT job_id, kind, started_at
            FROM sync_jobs 
            WHERE status = 'running'
            AND datetime(started_at) < datetime('now', '-1 hour')
        """)
        orphaned = cursor.fetchall()
        
        if orphaned:
            print("Jobs orfãos encontrados:")
            for job in orphaned:
                print(f"  {job[0]} | {job[1]} | {job[2]}")
            
            # Marcar como error (job orfão)
            conn.execute("""
                UPDATE sync_jobs 
                SET status = 'error', 
                    finished_at = datetime('now'),
                    updated_at = datetime('now')
                WHERE status = 'running'
                AND datetime(started_at) < datetime('now', '-1 hour')
            """)
            
            print(f"✅ {len(orphaned)} job(s) orfão(s) limpo(s)")
        else:
            print("Nenhum job orfão encontrado")
    
    # Verificar status após limpeza
    running_job = get_running_job()
    if running_job:
        print(f"❌ Ainda há job rodando: {running_job['job_id']}")
    else:
        print("✅ Nenhum job em execução - pronto para nova sincronização")

if __name__ == "__main__":
    clean_orphaned_jobs()
