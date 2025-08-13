"""
Testes básicos (smoke tests) para a camada de persistência SQLite.

Estes testes verificam se a funcionalidade básica do banco está funcionando.
"""

import os
import tempfile
import pytest
import json
from datetime import datetime

from app.core.db import get_conn, init_database, get_database_info
from app.services.repository import Repository


class TestDatabase:
    """Testes básicos do banco SQLite."""

    def test_database_connection(self):
        """Testa se consegue abrir conexão com banco."""
        conn = get_conn()
        assert conn is not None

        # Testa query simples
        cursor = conn.execute("SELECT 1 as test")
        result = cursor.fetchone()
        assert result["test"] == 1

    def test_database_initialization(self):
        """Testa se inicialização do banco funciona."""
        # Inicializar database
        init_database()

        # Verificar se tabelas foram criadas
        conn = get_conn()

        # Listar tabelas
        cursor = conn.execute(
            """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """
        )
        tables = [row["name"] for row in cursor.fetchall()]

        expected_tables = {"orders", "equipments", "technicians", "sync_state"}
        assert expected_tables.issubset(set(tables))

    def test_database_info(self):
        """Testa se consegue obter informações do banco."""
        info = get_database_info()

        assert "database_path" in info
        assert "database_exists" in info
        assert "tables" in info

        # Verificar tabelas
        tables = info["tables"]
        assert "orders" in tables
        assert "equipments" in tables
        assert "technicians" in tables
        assert "sync_state" in tables

    def test_orders_crud(self):
        """Testa operações CRUD básicas para ordens."""
        # Dados de teste
        test_orders = [
            {
                "id": 999901,
                "chamados": 1001,
                "data_criacao": "2025-08-12T10:00:00",
                "ordem_servico": {"id": 1001, "numero": "TEST-001", "estado": 1, "tipo_servico": 3},
                "responsavel_id": 1,
            },
            {
                "id": 999902,
                "chamados": 1002,
                "data_criacao": "2025-08-12T11:00:00",
                "ordem_servico": {"id": 1002, "numero": "TEST-002", "estado": 2, "tipo_servico": 1},
                "responsavel_id": 2,
            },
        ]

        # Salvar dados
        saved_count = Repository.save_orders(test_orders)
        assert saved_count == 2

        # Buscar dados
        df = Repository.get_orders(limit=10)
        assert len(df) >= 2

        # Verificar se dados estão corretos
        test_ids = {999901, 999902}
        db_ids = set(df[df["id"].isin(test_ids)]["id"].tolist())
        assert test_ids.issubset(db_ids)

        # Testar filtros de estado
        df_estado_1 = Repository.get_orders(estados=[1], limit=10)
        if len(df_estado_1) > 0:
            # Verificar se todos têm estado 1
            for _, row in df_estado_1.iterrows():
                if row["id"] in test_ids:
                    assert row["ordem_servico"]["estado"] == 1

    def test_equipments_crud(self):
        """Testa operações CRUD básicas para equipamentos."""
        # Dados de teste
        test_equipments = [
            {
                "id": 999801,
                "descricao": "Equipamento Teste 1",
                "fabricante": "Teste Corp",
                "modelo": "Model-1",
                "proprietario": 1,
                "updated_at": "2025-08-12T10:00:00",
            },
            {
                "id": 999802,
                "descricao": "Equipamento Teste 2",
                "fabricante": "Teste Corp",
                "modelo": "Model-2",
                "proprietario": 2,
                "updated_at": "2025-08-12T11:00:00",
            },
        ]

        # Salvar dados
        saved_count = Repository.save_equipments(test_equipments)
        assert saved_count == 2

        # Buscar dados
        df = Repository.get_equipments(limit=10)
        assert len(df) >= 2

        # Verificar se dados estão corretos
        test_ids = {999801, 999802}
        db_ids = set(df[df["id"].isin(test_ids)]["id"].tolist())
        assert test_ids.issubset(db_ids)

    def test_sync_state(self):
        """Testa operações de estado de sincronização."""
        resource = "test_resource"

        # Verificar que não existe inicialmente
        state = Repository.get_sync_state(resource)
        assert state is None

        # Criar estado
        Repository.update_sync_state(
            resource=resource, last_updated_at="2025-08-12T10:00:00", total_records=100
        )

        # Verificar que foi criado
        state = Repository.get_sync_state(resource)
        assert state is not None
        assert state["resource"] == resource
        assert state["last_updated_at"] == "2025-08-12T10:00:00"
        assert state["total_records"] == 100

        # Atualizar estado
        Repository.update_sync_state(resource=resource, total_records=200)

        # Verificar atualização
        state = Repository.get_sync_state(resource)
        assert state["total_records"] == 200
        assert state["last_updated_at"] == "2025-08-12T10:00:00"  # Não mudou

    def test_data_freshness(self):
        """Testa verificação de frescor dos dados."""
        resource = "test_freshness"

        # Dados não frescos (não existem)
        assert not Repository.is_data_fresh(resource)

        # Criar dados frescos (agora)
        Repository.update_sync_state(resource, total_records=50)
        assert Repository.is_data_fresh(resource, max_age_hours=1)

        # Dados não frescos (idade muito restritiva)
        assert not Repository.is_data_fresh(resource, max_age_hours=0)


def test_integration_full_cycle():
    """Teste de integração que simula ciclo completo."""
    # 1. Inicializar banco
    init_database()

    # 2. Verificar informações
    info = get_database_info()
    assert info["database_exists"]

    # 3. Salvar alguns dados
    orders = [
        {
            "id": 888801,
            "chamados": 8001,
            "data_criacao": "2025-08-12T14:00:00",
            "ordem_servico": {"id": 8001, "numero": "INT-001", "estado": 1},
            "responsavel_id": 1,
        }
    ]

    saved = Repository.save_orders(orders)
    assert saved == 1

    # 4. Atualizar sync state
    Repository.update_sync_state("orders", total_records=saved)

    # 5. Verificar que dados estão frescos
    assert Repository.is_data_fresh("orders")

    # 6. Buscar dados
    df = Repository.get_orders(limit=1)
    assert len(df) >= 1

    print("✅ Teste de integração completo passou!")


if __name__ == "__main__":
    # Executar teste de integração
    test_integration_full_cycle()

    # Mostrar informações do banco
    info = get_database_info()
    print("\n📊 Informações do banco:")
    print(f"  - Caminho: {info['database_path']}")
    print(f"  - Existe: {info['database_exists']}")
    print(f"  - Tamanho: {info.get('database_size_mb', 0)} MB")
    print(f"  - Tabelas: {info.get('tables', {})}")
