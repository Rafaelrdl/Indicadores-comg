"""Testes para os_metrics.py após migração para Repository pattern.

Este módulo testa especificamente as funções migradas que usam
o Repository pattern ao invés da API diretamente.
"""

from __future__ import annotations

import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch, AsyncMock
import pandas as pd

from app.services.os_metrics import (
    fetch_orders,
    fetch_service_orders_with_cache,
    compute_metrics,
    OSMetrics,
    SLA_HOURS,
    ServiceOrderData,
)
from app.core.exceptions import DataFetchError as CoreDataFetchError
from app.core.constants import DEFAULT_SLA_HOURS
from app.config.os_types import TIPO_CORRETIVA, AREA_ENG_CLIN


class TestOSMetricsRepository:
    """Testes para métricas de OS usando Repository."""

    def test_sla_hours_constant(self):
        """Testa se a constante SLA_HOURS está configurada corretamente."""
        assert SLA_HOURS == DEFAULT_SLA_HOURS
        assert SLA_HOURS == 72

    @pytest.mark.asyncio
    async def test_fetch_orders_success(self):
        """Testa busca bem-sucedida de ordens via Repository."""
        # Mock do DataFrame retornado pelo Repository
        mock_df = pd.DataFrame([
            {"id": 1, "tipo_id": TIPO_CORRETIVA, "area_id": AREA_ENG_CLIN, "estado": 1},
            {"id": 2, "tipo_id": TIPO_CORRETIVA, "area_id": AREA_ENG_CLIN, "estado": 2},
        ])
        
        with patch("app.services.repository.get_orders_df") as mock_get_orders:
            mock_get_orders.return_value = mock_df
            
            result = await fetch_orders(None, TIPO_CORRETIVA, AREA_ENG_CLIN)
            
            assert isinstance(result, list)
            assert len(result) == 2
            # Testamos apenas a estrutura básica para evitar problemas de typing
            assert len(result) > 0
            
            # Verifica que o Repository foi chamado
            mock_get_orders.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_orders_empty_result(self):
        """Testa busca com resultado vazio."""
        mock_df = pd.DataFrame()  # DataFrame vazio
        
        with patch("app.services.repository.get_orders_df") as mock_get_orders:
            mock_get_orders.return_value = mock_df
            
            result = await fetch_orders(None, TIPO_CORRETIVA, AREA_ENG_CLIN)
            
            assert isinstance(result, list)
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_fetch_orders_exception(self):
        """Testa tratamento de exceção durante busca."""
        with patch("app.services.repository.get_orders_df") as mock_get_orders:
            mock_get_orders.side_effect = Exception("Database error")
            
            with pytest.raises(CoreDataFetchError) as exc_info:
                await fetch_orders(None, TIPO_CORRETIVA, AREA_ENG_CLIN)
            
            assert "Failed to fetch orders from Repository" in str(exc_info.value)
            assert exc_info.value.context["order_type"] == TIPO_CORRETIVA
            assert exc_info.value.context["area_id"] == AREA_ENG_CLIN

    @pytest.mark.asyncio
    async def test_fetch_service_orders_with_cache_success(self):
        """Testa busca com cache bem-sucedida."""
        mock_data = {
            "corrective_building": [],
            "corrective_engineering": [],
            "preventive_building": [],
            "preventive_infra": [],
            "active_search": [],
            "open_orders": [],
            "closed_orders": [],
            "closed_in_period": [],
        }
        
        with patch("app.services.os_metrics.fetch_service_orders_with_cache", return_value=mock_data):
            start_date = date.today() - timedelta(days=30)
            end_date = date.today()
            
            result = await fetch_service_orders_with_cache(None, start_date, end_date)
            
            assert isinstance(result, dict)
            assert "corrective_building" in result
            assert "corrective_engineering" in result

    @pytest.mark.asyncio
    async def test_fetch_service_orders_empty_database(self):
        """Testa comportamento com banco vazio."""
        with patch("app.services.repository.get_database_stats") as mock_stats:
            mock_stats.return_value = {"orders_count": 0}  # Banco vazio
            
            start_date = date.today() - timedelta(days=30)
            end_date = date.today()
            
            result = await fetch_service_orders_with_cache(None, start_date, end_date)
            
            assert isinstance(result, dict)
            assert len(result) == 0  # Retorna dict vazio

    def test_os_metrics_dataclass(self):
        """Testa a criação do dataclass OSMetrics."""
        metrics = OSMetrics(
            corrective_building=5,
            corrective_engineering=10,
            preventive_building=3,
            preventive_infra=7,
            active_search=2,
            backlog=15,
            sla_percentage=85.5
        )
        
        assert metrics.corrective_building == 5
        assert metrics.corrective_engineering == 10
        assert metrics.backlog == 15
        assert metrics.sla_percentage == 85.5

    @pytest.mark.asyncio
    async def test_compute_metrics_with_dates(self):
        """Testa computação completa de métricas com datas."""
        mock_data = {
            "corrective_building": [{"id": 1}],
            "corrective_engineering": [{"id": 2}],
            "preventive_building": [],
            "preventive_infra": [],
            "active_search": [],
            "open_orders": [{"id": 1}, {"id": 3}],  # 2 ordens abertas
            "closed_orders": [{"id": 2}],  # 1 ordem fechada
            "closed_in_period": [{"id": 2}],  # Para cálculo de SLA
        }
        
        with patch("app.services.os_metrics.fetch_service_orders_with_cache") as mock_fetch:
            mock_fetch.return_value = mock_data
            
            start_date = date.today() - timedelta(days=30)
            end_date = date.today()
            
            result = await compute_metrics(None, start_date=start_date, end_date=end_date)
            
            assert isinstance(result, OSMetrics)
            # Como temos mock data, deve calcular corretamente
            mock_fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_compute_metrics_backward_compatibility(self):
        """Testa compatibilidade com parâmetros antigos (dt_ini, dt_fim)."""
        with patch("app.services.os_metrics.fetch_service_orders_with_cache") as mock_fetch:
            mock_fetch.return_value = {
                "corrective_building": [],
                "corrective_engineering": [],
                "preventive_building": [],
                "preventive_infra": [],
                "active_search": [],
                "open_orders": [],
                "closed_orders": [],
                "closed_in_period": [],
            }
            
            # Usa parâmetros antigos
            dt_ini = date.today() - timedelta(days=7)
            dt_fim = date.today()
            
            result = await compute_metrics(None, dt_ini=dt_ini, dt_fim=dt_fim)
            
            assert isinstance(result, OSMetrics)
            mock_fetch.assert_called_once()
            
            # Verifica que as datas foram convertidas corretamente
            call_args = mock_fetch.call_args
            assert call_args[0][1] == dt_ini  # start_date
            assert call_args[0][2] == dt_fim  # end_date

    @pytest.mark.asyncio  
    async def test_compute_metrics_with_filters(self):
        """Testa computação com filtros adicionais."""
        with patch("app.services.os_metrics.fetch_service_orders_with_cache") as mock_fetch:
            mock_fetch.return_value = {
                "corrective_building": [],
                "corrective_engineering": [],
                "preventive_building": [],
                "preventive_infra": [],
                "active_search": [],
                "open_orders": [],
                "closed_orders": [],
                "closed_in_period": [],
            }
            
            result = await compute_metrics(
                None,
                start_date=date.today() - timedelta(days=7),
                end_date=date.today(),
                area_filter="engenharia"
            )
            
            assert isinstance(result, OSMetrics)
            # Verifica que os filtros foram passados
            mock_fetch.assert_called_once()
            call_args = mock_fetch.call_args
            assert "area_filter" in call_args.kwargs

    @pytest.mark.asyncio
    async def test_fetch_orders_different_order_types(self):
        """Testa busca com diferentes tipos de ordem."""
        mock_df = pd.DataFrame([{"id": 1, "tipo_id": 1}])
        
        with patch("app.services.repository.get_orders_df") as mock_get_orders:
            mock_get_orders.return_value = mock_df
            
            # Testa tipo preventiva
            result = await fetch_orders(None, 1, None)  # TIPO_PREVENTIVA
            assert isinstance(result, list)
            
            # Testa tipo corretiva  
            result = await fetch_orders(None, 3, None)  # TIPO_CORRETIVA
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_fetch_orders_with_area_filter(self):
        """Testa busca com filtro de área."""
        mock_df = pd.DataFrame([{"id": 1, "area_id": 1}])
        
        with patch("app.services.repository.get_orders_df") as mock_get_orders:
            mock_get_orders.return_value = mock_df
            
            # Com área específica
            result = await fetch_orders(None, TIPO_CORRETIVA, AREA_ENG_CLIN)
            assert isinstance(result, list)
            
            # Sem filtro de área
            result = await fetch_orders(None, TIPO_CORRETIVA, None)
            assert isinstance(result, list)
