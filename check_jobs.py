#!/usr/bin/env python3
"""Script para verificar o status dos jobs de sincronização."""

from app.core.db import get_conn
from app.services.sync_jobs import get_running_job, has_running_job

def main():
    print("=== STATUS DOS JOBS ===")
    
    running_job = get_running_job()
    if running_job:
        print("Job em execução encontrado:")
        print(f"  ID: {running_job['job_id']}")
        print(f"  Tipo: {running_job['kind']}")
        print(f"  Status: {running_job['status']}")
        print(f"  Iniciado em: {running_job['started_at']}")
        print(f"  Atualizado em: {running_job['updated_at']}")
    else:
        print("Nenhum job em execução encontrado")
    
    print(f"Has running job: {has_running_job()}")
    
    print("\n=== TODOS OS JOBS ===")
    with get_conn() as conn:
        cursor = conn.execute("""
            SELECT job_id, kind, status, started_at, finished_at 
            FROM sync_jobs 
            ORDER BY started_at DESC 
            LIMIT 10
        """)
        jobs = cursor.fetchall()
        
        if jobs:
            print("ID | Tipo | Status | Iniciado | Finalizado")
            print("-" * 60)
            for job in jobs:
                print(f"{job[0]} | {job[1]} | {job[2]} | {job[3]} | {job[4] or 'N/A'}")
        else:
            print("Nenhum job encontrado na base")

    print("\n=== CONTAGEM POR STATUS ===")
    with get_conn() as conn:
        cursor = conn.execute("""
            SELECT status, COUNT(*) 
            FROM sync_jobs 
            GROUP BY status
        """)
        counts = cursor.fetchall()
        
        if counts:
            for status, count in counts:
                print(f"  {status}: {count}")
        else:
            print("Nenhum job encontrado")

if __name__ == "__main__":
    main()
