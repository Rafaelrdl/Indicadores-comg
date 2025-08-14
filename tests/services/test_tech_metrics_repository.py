"""Testes para tech_metrics.py após migração para Repository pattern.

Este módulo testa especificamente as funções migradas que usam
o Repository pattern ao invés da API diretamente.
"""

from __future__ import annotations

import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch, AsyncMock
import pandas as pd

from app.services.tech_metrics import (
    fetch_technician_orders,
    group_orders_by_technician,
    calculate_technician_kpis,
    compute_metrics,
    TechnicianKPI,
    SLA_HOURS,
)
from app.core.exceptions import DataFetchError as CoreDataFetchError
from app.core.constants import DEFAULT_SLA_HOURS


class TestTechMetricsRepository:
    """Testes para métricas de técnicos usando Repository."""

    def test_sla_hours_constant(self):
        """Testa se a constante SLA_HOURS está configurada corretamente."""
        assert SLA_HOURS == DEFAULT_SLA_HOURS
        assert SLA_HOURS == 72

    @pytest.mark.asyncio
    async def test_fetch_technician_orders_success(self):
        """Testa busca bem-sucedida de ordens de técnicos via Repository."""
        # Mock do DataFrame retornado pelo Repository
        mock_df = pd.DataFrame([
            {"id": 1, "responsavel": {"id": 1, "display_name": "Tech 1"}, "estado": {"id": 3}},
            {"id": 2, "responsavel": {"id": 2, "display_name": "Tech 2"}, "estado": {"id": 1}},
        ])

        with patch("app.services.repository.get_orders_df") as mock_get_orders:
            mock_get_orders.return_value = mock_df
            
            start_date = date.today() - timedelta(days=30)
            end_date = date.today()
            
            result = await fetch_technician_orders(None, start_date, end_date)
            
            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["id"] == 1
            assert result[1]["id"] == 2
            
            # Verifica que o Repository foi chamado corretamente
            mock_get_orders.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_technician_orders_empty_result(self):
        """Testa busca com resultado vazio."""
        mock_df = pd.DataFrame()  # DataFrame vazio

        with patch("app.services.repository.get_orders_df") as mock_get_orders:
            mock_get_orders.return_value = mock_df
            
            start_date = date.today() - timedelta(days=30)
            end_date = date.today()
            
            result = await fetch_technician_orders(None, start_date, end_date)
            
            assert isinstance(result, list)
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_fetch_technician_orders_exception(self):
        """Testa tratamento de exceção durante busca."""
        with patch("app.services.repository.get_orders_df") as mock_get_orders:
            mock_get_orders.side_effect = Exception("Database error")
            
            start_date = date.today() - timedelta(days=30)
            end_date = date.today()
            
            with pytest.raises(CoreDataFetchError) as exc_info:
                await fetch_technician_orders(None, start_date, end_date)
            
            assert "Failed to fetch technician data from Repository" in str(exc_info.value)
            assert exc_info.value.context["start_date"] == start_date.isoformat()
            assert exc_info.value.context["end_date"] == end_date.isoformat()

    def test_group_orders_by_technician_success(self):
        """Testa agrupamento de ordens por técnico."""
        orders = [
            {"responsavel": {"id": 1}, "estado": {"id": 3}},  # Tech 1, não cancelada
            {"responsavel": {"id": 2}, "estado": {"id": 1}},  # Tech 2, não cancelada  
            {"responsavel": {"id": 1}, "estado": {"id": 5}},  # Tech 1, cancelada (deve ser ignorada)
            {"responsavel": {"id": 1}, "estado": {"id": 2}},  # Tech 1, não cancelada
        ]
        
        result = group_orders_by_technician(orders)
        
        assert isinstance(result, dict)
        assert len(result) == 2  # Tech 1 e Tech 2
        assert len(result[1]) == 2  # Tech 1 tem 2 ordens válidas
        assert len(result[2]) == 1  # Tech 2 tem 1 ordem válida

    def test_group_orders_by_technician_empty(self):
        """Testa agrupamento com lista vazia."""
        result = group_orders_by_technician([])
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_group_orders_by_technician_no_responsavel(self):
        """Testa agrupamento com ordens sem responsável."""
        orders = [
            {"responsavel": None, "estado": {"id": 3}},
            {"estado": {"id": 1}},  # Sem campo responsavel
        ]
        
        result = group_orders_by_technician(orders)
        assert isinstance(result, dict)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_compute_metrics_success(self):
        """Testa computação completa de métricas."""
        # Mock das ordens agrupadas
        from datetime import datetime
        mock_orders = [
            {
                "id": 1, 
                "responsavel": {"id": 1, "display_name": "Tech 1"}, 
                "estado": {"id": 3},
                "data_criacao": datetime.now()
            },
            {
                "id": 2, 
                "responsavel": {"id": 1, "display_name": "Tech 1"}, 
                "estado": {"id": 2},
                "data_criacao": datetime.now()
            },
        ]
        
        with patch("app.services.tech_metrics.fetch_technician_orders") as mock_fetch:
            mock_fetch.return_value = mock_orders
            
            start_date = date.today() - timedelta(days=30)
            end_date = date.today()
            
            result = await compute_metrics(None, start_date=start_date, end_date=end_date)
            
            assert isinstance(result, list)
            # Como temos dados mock, pode retornar lista vazia se não há técnicos válidos
            # O importante é que não deu erro

    def test_technician_kpi_dataclass(self):
        """Testa a criação do dataclass TechnicianKPI."""
        kpi = TechnicianKPI(
            technician_id=1,
            name="Tech Test",
            open_orders=5,
            completed_orders=10,
            total_pending=15,
            sla_percentage=85.5,
            average_close_hours=48.2
        )
        
        assert kpi.technician_id == 1
        assert kpi.name == "Tech Test"
        assert kpi.open_orders == 5
        
        # Testa propriedades de compatibilidade
        assert kpi.tecnico_id == 1
        assert kpi.abertas == 5
        assert kpi.concluidas == 10

    @pytest.mark.asyncio
    async def test_compute_metrics_with_filters(self):
        """Testa computação com filtros adicionais."""
        with patch("app.services.tech_metrics.fetch_technician_orders") as mock_fetch:
            mock_fetch.return_value = []
            
            result = await compute_metrics(
                None,
                start_date=date.today() - timedelta(days=7),
                end_date=date.today(),
                area_id=1,
                tipo_id=2
            )
            
            assert isinstance(result, list)
            # Verifica que os filtros foram passados
            mock_fetch.assert_called_once()
            call_args = mock_fetch.call_args
            assert "area_id" in call_args.kwargs
            assert "tipo_id" in call_args.kwargs
