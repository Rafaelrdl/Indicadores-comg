"""
Testes para o sistema de sincronização incremental.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from app.core.db import get_conn, init_database
from app.services.sync.ingest import BackfillSync, run_backfill
from app.services.sync.delta import (
    IncrementalSync,
    run_incremental_sync,
    should_run_incremental_sync,
)
from app.services.sync._upsert import upsert_records, update_sync_state, get_last_sync_info


class TestUpsertOperations:
    """Testa operações básicas de upsert."""

    def test_upsert_records_basic(self):
        """Testa upsert básico de registros."""
        # Inicializar banco
        init_database()
        conn = get_conn()

        # Dados de teste
        test_records = [
            {
                "id": 99901,
                "chamados": 1001,
                "data_criacao": "2025-08-12T10:00:00",
                "ordem_servico": {"numero": "TEST-001", "estado": 1},
                "responsavel_id": 1,
                "updated_at": "2025-08-12T10:00:00",
            },
            {
                "id": 99902,
                "chamados": 1002,
                "data_criacao": "2025-08-12T11:00:00",
                "ordem_servico": {"numero": "TEST-002", "estado": 2},
                "responsavel_id": 2,
                "updated_at": "2025-08-12T11:00:00",
            },
        ]

        # Fazer upsert
        count = upsert_records(conn, "orders", test_records)
        assert count == 2

        # Verificar se registros foram salvos
        cursor = conn.execute("SELECT id, payload FROM orders WHERE id IN (99901, 99902)")
        rows = cursor.fetchall()
        assert len(rows) == 2

        # Verificar conteúdo
        for row in rows:
            payload = json.loads(row["payload"])
            assert payload["id"] in [99901, 99902]
            assert "ordem_servico" in payload

    def test_upsert_duplicate_handling(self):
        """Testa se duplicatas são tratadas corretamente (REPLACE)."""
        init_database()
        conn = get_conn()

        # Primeiro insert
        record_v1 = {
            "id": 99903,
            "chamados": 1003,
            "data_criacao": "2025-08-12T10:00:00",
            "updated_at": "2025-08-12T10:00:00",
        }

        upsert_records(conn, "orders", [record_v1])

        # Segundo insert com mesmo ID (deve substituir)
        record_v2 = {
            "id": 99903,
            "chamados": 1003,
            "data_criacao": "2025-08-12T12:00:00",  # Diferente
            "updated_at": "2025-08-12T12:00:00",  # Diferente
        }

        upsert_records(conn, "orders", [record_v2])

        # Verificar que só existe 1 registro e é o mais recente
        cursor = conn.execute("SELECT payload FROM orders WHERE id = 99903")
        row = cursor.fetchone()
        payload = json.loads(row["payload"])

        assert payload["data_criacao"] == "2025-08-12T12:00:00"
        assert payload["updated_at"] == "2025-08-12T12:00:00"

    def test_sync_state_operations(self):
        """Testa operações de estado de sincronização."""
        init_database()
        conn = get_conn()

        # Teste update_sync_state
        update_sync_state(
            conn,
            "test_resource",
            last_updated_at="2025-08-12T10:00:00",
            last_id=1000,
            total_records=50,
            sync_type="backfill",
        )

        # Teste get_last_sync_info
        sync_info = get_last_sync_info(conn, "test_resource")
        assert sync_info is not None
        assert sync_info["resource"] == "test_resource"
        assert sync_info["last_updated_at"] == "2025-08-12T10:00:00"
        assert sync_info["last_id"] == 1000
        assert sync_info["total_records"] == 50
        assert sync_info["sync_type"] == "backfill"


class TestBackfillSync:
    """Testa sistema de backfill."""

    @pytest.mark.asyncio
    async def test_sync_orders_basic(self):
        """Testa sincronização básica de ordens."""
        # Mock client
        mock_client = Mock()
        mock_client.list_chamados = AsyncMock(
            return_value=[
                Mock(
                    model_dump=Mock(
                        return_value={
                            "id": 99910,
                            "chamados": 1010,
                            "data_criacao": "2025-08-12T10:00:00",
                            "updated_at": "2025-08-12T10:00:00",
                        }
                    )
                ),
                Mock(
                    model_dump=Mock(
                        return_value={
                            "id": 99911,
                            "chamados": 1011,
                            "data_criacao": "2025-08-12T11:00:00",
                            "updated_at": "2025-08-12T11:00:00",
                        }
                    )
                ),
            ]
        )

        # Inicializar banco
        init_database()

        # Executar sync
        sync = BackfillSync(mock_client)
        result = await sync.sync_orders()

        assert result == 2

        # Verificar se dados foram salvos
        conn = get_conn()
        cursor = conn.execute("SELECT COUNT(*) FROM orders WHERE id IN (99910, 99911)")
        count = cursor.fetchone()[0]
        assert count == 2

    @pytest.mark.asyncio
    async def test_run_backfill_function(self):
        """Testa função de conveniência run_backfill."""
        # Mock client
        mock_client = Mock()
        mock_client.list_chamados = AsyncMock(
            return_value=[
                Mock(
                    model_dump=Mock(
                        return_value={
                            "id": 99920,
                            "chamados": 1020,
                            "data_criacao": "2025-08-12T10:00:00",
                        }
                    )
                )
            ]
        )

        init_database()

        # Executar
        results = await run_backfill(mock_client, ["orders"])

        assert "orders" in results
        assert results["orders"] == 1


class TestIncrementalSync:
    """Testa sincronização incremental."""

    @pytest.mark.asyncio
    async def test_sync_orders_incremental_first_run(self):
        """Testa primeira execução de sync incremental."""
        # Mock client
        mock_client = Mock()
        mock_client.list_chamados = AsyncMock(
            return_value=[
                Mock(
                    model_dump=Mock(
                        return_value={
                            "id": 99930,
                            "chamados": 1030,
                            "data_criacao": "2025-08-12T10:00:00",
                            "updated_at": "2025-08-12T10:00:00",
                        }
                    )
                )
            ]
        )

        init_database()

        # Executar (primeira vez - deve buscar últimas 24h)
        sync = IncrementalSync(mock_client)
        result = await sync.sync_orders_incremental()

        assert result == 1

        # Verificar filtros aplicados (deve incluir data_criacao__gte)
        call_args = mock_client.list_chamados.call_args[0][0]
        assert "data_criacao__gte" in call_args

    @pytest.mark.asyncio
    async def test_sync_orders_incremental_subsequent_run(self):
        """Testa execução subsequente usando timestamp."""
        # Preparar estado anterior
        init_database()
        conn = get_conn()

        update_sync_state(
            conn,
            "orders",
            last_updated_at="2025-08-12T09:00:00",
            last_id=99900,
            total_records=100,
            sync_type="incremental",
        )

        # Mock client
        mock_client = Mock()
        mock_client.list_chamados = AsyncMock(
            return_value=[
                Mock(
                    model_dump=Mock(
                        return_value={
                            "id": 99931,
                            "chamados": 1031,
                            "data_criacao": "2025-08-12T10:00:00",
                            "updated_at": "2025-08-12T10:00:00",
                        }
                    )
                )
            ]
        )

        # Executar
        sync = IncrementalSync(mock_client)
        result = await sync.sync_orders_incremental()

        assert result == 1

        # Verificar filtros (deve usar updated_at__gt)
        call_args = mock_client.list_chamados.call_args[0][0]
        assert "updated_at__gt" in call_args
        assert call_args["updated_at__gt"] == "2025-08-12T09:00:00"

    def test_should_run_incremental_sync(self):
        """Testa lógica de decisão para sync incremental."""
        init_database()
        conn = get_conn()

        # Caso 1: Nunca sincronizou (deve sincronizar)
        assert should_run_incremental_sync("never_synced_resource") == True

        # Caso 2: Sincronizou recentemente (não deve sincronizar)
        update_sync_state(conn, "fresh_resource", total_records=50, sync_type="incremental")
        assert should_run_incremental_sync("fresh_resource", max_age_hours=2) == False

        # Caso 3: Sincronizou há muito tempo (deve sincronizar)
        old_time = (datetime.now() - timedelta(hours=5)).isoformat()
        conn.execute(
            "UPDATE sync_state SET synced_at = ? WHERE resource = ?", (old_time, "fresh_resource")
        )
        conn.commit()
        assert should_run_incremental_sync("fresh_resource", max_age_hours=2) == True


@pytest.mark.asyncio
async def test_integration_backfill_then_incremental():
    """Teste de integração: backfill seguido de incremental."""
    # Mock client com dados diferentes para cada chamada
    mock_client = Mock()

    # Primeira chamada (backfill)
    backfill_data = [
        Mock(
            model_dump=Mock(
                return_value={
                    "id": 99940,
                    "chamados": 1040,
                    "data_criacao": "2025-08-12T10:00:00",
                    "updated_at": "2025-08-12T10:00:00",
                }
            )
        )
    ]

    # Segunda chamada (incremental)
    incremental_data = [
        Mock(
            model_dump=Mock(
                return_value={
                    "id": 99941,
                    "chamados": 1041,
                    "data_criacao": "2025-08-12T11:00:00",
                    "updated_at": "2025-08-12T11:00:00",
                }
            )
        )
    ]

    mock_client.list_chamados = AsyncMock(side_effect=[backfill_data, incremental_data])

    init_database()

    # 1. Executar backfill
    backfill_results = await run_backfill(mock_client, ["orders"])
    assert backfill_results["orders"] == 1

    # 2. Verificar estado do sync
    conn = get_conn()
    sync_info = get_last_sync_info(conn, "orders")
    assert sync_info is not None
    assert sync_info["sync_type"] == "backfill"

    # 3. Executar incremental
    incremental_results = await run_incremental_sync(mock_client, ["orders"])
    assert incremental_results["orders"] == 1

    # 4. Verificar estado final
    final_sync_info = get_last_sync_info(conn, "orders")
    assert final_sync_info["sync_type"] == "incremental"

    # 5. Verificar total de registros no banco
    cursor = conn.execute("SELECT COUNT(*) FROM orders WHERE id IN (99940, 99941)")
    total_count = cursor.fetchone()[0]
    assert total_count == 2


if __name__ == "__main__":
    # Executar testes básicos
    test_upsert = TestUpsertOperations()
    test_upsert.test_upsert_records_basic()
    test_upsert.test_upsert_duplicate_handling()
    test_upsert.test_sync_state_operations()

    print("✅ Todos os testes de upsert passaram!")

    # Teste de integração
    asyncio.run(test_integration_backfill_then_incremental())
    print("✅ Teste de integração passou!")
