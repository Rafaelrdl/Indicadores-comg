"""
Sistema de gerenciamento de jobs de sincronização com progresso.

Este módulo fornece funcionalidades para criar, atualizar e monitorar
o progresso de jobs de sincronização (delta e backfill).
"""

import time
from typing import Any

from app.core.db import get_conn
from app.core.logging import app_logger


def create_job(kind: str, start_page: int = 1) -> str:
    """
    Cria um novo job de sincronização.

    Args:
        kind: Tipo do job ('delta' ou 'backfill')
        start_page: Página inicial da sincronização

    Returns:
        str: ID único do job criado
    """
    job_id = f"{kind}-{int(time.time() * 1000)}"

    try:
        with get_conn() as conn:
            conn.execute(
                """
                INSERT INTO sync_jobs(
                    job_id, kind, status, processed, total, percent,
                    last_page_synced, current_page, total_pages,
                    started_at, updated_at
                )
                VALUES (?, ?, 'running', 0, NULL, NULL, 0, ?, NULL, datetime('now'), datetime('now'))
            """,
                (job_id, kind, start_page),
            )

        app_logger.log_info(f"🆕 Job de sincronização criado: {job_id} (página inicial: {start_page})")
        return job_id

    except Exception as e:
        app_logger.log_error(e, {"context": "create_job", "job_id": job_id, "kind": kind})
        raise


def update_job(job_id: str, processed: int, total: int | None = None) -> None:
    """
    Atualiza o progresso de um job.

    Args:
        job_id: ID do job
        processed: Número de itens processados
        total: Total de itens (opcional, se conhecido)
    """
    try:
        with get_conn() as conn:
            if total is not None:
                # Atualizar com total conhecido
                conn.execute(
                    """
                    UPDATE sync_jobs
                    SET processed = ?, total = ?, updated_at = datetime('now')
                    WHERE job_id = ? AND status = 'running'
                """,
                    (processed, total, job_id),
                )
            else:
                # Atualizar apenas processados
                conn.execute(
                    """
                    UPDATE sync_jobs
                    SET processed = ?, updated_at = datetime('now')
                    WHERE job_id = ? AND status = 'running'
                """,
                    (processed, job_id),
                )

    except Exception as e:
        app_logger.log_error(
            e, {"context": "update_job", "job_id": job_id, "processed": processed, "total": total}
        )


def finish_job(job_id: str, status: str) -> None:
    """
    Finaliza um job com sucesso ou erro.

    Args:
        job_id: ID do job
        status: Status final ('success' ou 'error')
    """
    try:
        with get_conn() as conn:
            conn.execute(
                """
                UPDATE sync_jobs
                SET status = ?, finished_at = datetime('now'), updated_at = datetime('now')
                WHERE job_id = ?
            """,
                (status, job_id),
            )

        app_logger.log_info(f"✅ Job finalizado: {job_id} - {status}")

    except Exception as e:
        app_logger.log_error(e, {"context": "finish_job", "job_id": job_id, "status": status})


def get_running_job(kind: str | None = None) -> dict[str, Any] | None:
    """
    Obtém o job atualmente em execução.

    Args:
        kind: Filtrar por tipo específico (opcional)

    Returns:
        Dict com dados do job ou None se não houver job rodando
    """
    try:
        with get_conn() as conn:
            if kind:
                cursor = conn.execute(
                    """
                    SELECT job_id, kind, status, total, processed, percent,
                           started_at, updated_at
                    FROM sync_jobs
                    WHERE status = 'running' AND kind = ?
                    ORDER BY started_at DESC
                    LIMIT 1
                """,
                    (kind,),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT job_id, kind, status, total, processed, percent,
                           started_at, updated_at
                    FROM sync_jobs
                    WHERE status = 'running'
                    ORDER BY started_at DESC
                    LIMIT 1
                """
                )

            row = cursor.fetchone()
            if row:
                return {
                    "job_id": row[0],
                    "kind": row[1],
                    "status": row[2],
                    "total": row[3],
                    "processed": row[4],
                    "percent": row[5],
                    "started_at": row[6],
                    "updated_at": row[7],
                }
            return None

    except Exception as e:
        app_logger.log_error(e, {"context": "get_running_job", "kind": kind})
        return None


def get_last_success_job(kind: str | None = None) -> dict[str, Any] | None:
    """
    Obtém o último job concluído com sucesso.

    Args:
        kind: Filtrar por tipo específico (opcional)

    Returns:
        Dict com dados do último job bem-sucedido
    """
    try:
        with get_conn() as conn:
            if kind:
                cursor = conn.execute(
                    """
                    SELECT job_id, kind, status, total, processed, percent,
                           started_at, finished_at
                    FROM sync_jobs
                    WHERE status = 'success' AND kind = ?
                    ORDER BY finished_at DESC
                    LIMIT 1
                """,
                    (kind,),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT job_id, kind, status, total, processed, percent,
                           started_at, finished_at
                    FROM sync_jobs
                    WHERE status = 'success'
                    ORDER BY finished_at DESC
                    LIMIT 1
                """
                )

            row = cursor.fetchone()
            if row:
                return {
                    "job_id": row[0],
                    "kind": row[1],
                    "status": row[2],
                    "total": row[3],
                    "processed": row[4],
                    "percent": row[5],
                    "started_at": row[6],
                    "finished_at": row[7],
                }
            return None

    except Exception as e:
        app_logger.log_error(e, {"context": "get_last_success_job", "kind": kind})
        return None


def has_running_job(kind: str | None = None) -> bool:
    """
    Verifica se há um job rodando.

    Args:
        kind: Filtrar por tipo específico (opcional)

    Returns:
        bool: True se há job rodando
    """
    running_job = get_running_job(kind)
    return running_job is not None


def cleanup_old_jobs(days: int = 7) -> int:
    """
    Remove jobs antigos para manter a tabela limpa.

    Args:
        days: Manter jobs dos últimos N dias

    Returns:
        int: Número de jobs removidos
    """
    try:
        with get_conn() as conn:
            cursor = conn.execute(
                f"""
                DELETE FROM sync_jobs
                WHERE status != 'running'
                AND datetime(started_at) < datetime('now', '-{days} days')
            """
            )

            deleted_count = cursor.rowcount
            if deleted_count > 0:
                app_logger.log_info(f"🧹 Removidos {deleted_count} jobs antigos (>{days} dias)")

            return deleted_count

    except Exception as e:
        app_logger.log_error(e, {"context": "cleanup_old_jobs", "days": days})
        return 0


def get_job_history(limit: int = 10) -> list[dict[str, Any]]:
    """
    Obtém histórico de jobs recentes.

    Args:
        limit: Número máximo de jobs a retornar

    Returns:
        Lista com histórico de jobs
    """
    try:
        with get_conn() as conn:
            cursor = conn.execute(
                """
                SELECT job_id, kind, status, total, processed, percent,
                       started_at, finished_at, updated_at
                FROM sync_jobs
                ORDER BY started_at DESC
                LIMIT ?
            """,
                (limit,),
            )

            jobs = []
            for row in cursor.fetchall():
                jobs.append(
                    {
                        "job_id": row[0],
                        "kind": row[1],
                        "status": row[2],
                        "total": row[3],
                        "processed": row[4],
                        "percent": row[5],
                        "started_at": row[6],
                        "finished_at": row[7],
                        "updated_at": row[8],
                    }
                )

            return jobs

    except Exception as e:
        app_logger.log_error(e, {"context": "get_job_history", "limit": limit})
        return []
