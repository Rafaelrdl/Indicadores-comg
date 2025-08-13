"""
Testes para o sistema de rastreamento de progresso de sincronização.

Testa a funcionalidade de criação, atualização e finalização de jobs
de sincronização com persistência de progresso em tempo real.
"""
import pytest
import sqlite3
from unittest.mock import Mock, patch, call
from datetime import datetime

from app.services.sync_jobs import (
    create_job, update_job, finish_job, get_running_job, 
    get_last_success_job, has_running_job, cleanup_old_jobs,
    get_job_history
)


class TestSyncJobsDatabase:
    """Testes para operações de banco de dados de jobs."""
    
    @pytest.fixture
    def mock_conn(self):
        """Mock de conexão SQLite."""
        conn = Mock(spec=sqlite3.Connection)
        conn.__enter__ = Mock(return_value=conn)
        conn.__exit__ = Mock(return_value=None)
        return conn
    
    @patch('app.services.sync_jobs.get_conn')
    def test_create_job_success(self, mock_get_conn, mock_conn):
        """Deve criar job com sucesso."""
        # Arrange
        mock_get_conn.return_value = mock_conn
        
        # Act
        job_id = create_job('delta')
        
        # Assert
        assert job_id.startswith('delta-')
        mock_conn.execute.assert_called_once()
        
        # Verificar SQL
        call_args = mock_conn.execute.call_args
        assert 'INSERT INTO sync_jobs' in call_args[0][0]
        assert call_args[0][1] == (job_id, 'delta')
    
    @patch('app.services.sync_jobs.get_conn')
    def test_create_job_handles_exception(self, mock_get_conn, mock_conn):
        """Deve tratar exceções na criação de job."""
        # Arrange
        mock_get_conn.return_value = mock_conn
        mock_conn.execute.side_effect = sqlite3.Error("Database error")
        
        # Act & Assert
        with pytest.raises(sqlite3.Error):
            create_job('delta')
    
    @patch('app.services.sync_jobs.get_conn')
    def test_update_job_with_total(self, mock_get_conn, mock_conn):
        """Deve atualizar job com total conhecido."""
        # Arrange
        mock_get_conn.return_value = mock_conn
        job_id = 'delta-123'
        
        # Act
        update_job(job_id, processed=50, total=100)
        
        # Assert
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args
        assert 'UPDATE sync_jobs' in call_args[0][0]
        assert 'total = ?' in call_args[0][0]
        assert call_args[0][1] == (50, 100, job_id)
    
    @patch('app.services.sync_jobs.get_conn')
    def test_update_job_without_total(self, mock_get_conn, mock_conn):
        """Deve atualizar job sem total."""
        # Arrange
        mock_get_conn.return_value = mock_conn
        job_id = 'delta-456'
        
        # Act
        update_job(job_id, processed=25)
        
        # Assert
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args
        assert 'UPDATE sync_jobs' in call_args[0][0]
        assert 'total = ?' not in call_args[0][0]
        assert call_args[0][1] == (25, job_id)
    
    @patch('app.services.sync_jobs.get_conn')
    def test_finish_job_success(self, mock_get_conn, mock_conn):
        """Deve finalizar job com sucesso."""
        # Arrange
        mock_get_conn.return_value = mock_conn
        job_id = 'delta-789'
        
        # Act
        finish_job(job_id, 'success')
        
        # Assert
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args
        assert 'UPDATE sync_jobs' in call_args[0][0]
        assert 'status = ?' in call_args[0][0]
        assert 'finished_at = datetime' in call_args[0][0]
        assert call_args[0][1] == ('success', job_id)
    
    @patch('app.services.sync_jobs.get_conn')
    def test_finish_job_error_status(self, mock_get_conn, mock_conn):
        """Deve finalizar job com status de erro."""
        # Arrange
        mock_get_conn.return_value = mock_conn
        job_id = 'backfill-999'
        
        # Act
        finish_job(job_id, 'error')
        
        # Assert
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args
        assert call_args[0][1] == ('error', job_id)


class TestSyncJobsQuery:
    """Testes para consultas de jobs."""
    
    @pytest.fixture
    def mock_conn(self):
        """Mock de conexão com cursor."""
        conn = Mock(spec=sqlite3.Connection)
        cursor = Mock()
        conn.execute.return_value = cursor
        conn.__enter__ = Mock(return_value=conn)
        conn.__exit__ = Mock(return_value=None)
        return conn, cursor
    
    @patch('app.services.sync_jobs.get_conn')
    def test_get_running_job_found(self, mock_get_conn):
        """Deve retornar job em execução."""
        # Arrange
        conn, cursor = Mock(), Mock()
        mock_get_conn.return_value = conn
        conn.__enter__ = Mock(return_value=conn)
        conn.__exit__ = Mock(return_value=None)
        conn.execute.return_value = cursor
        
        # Mock da linha retornada
        cursor.fetchone.return_value = (
            'delta-123', 'delta', 'running', 100, 50, 50,
            '2025-08-13T10:00:00', '2025-08-13T10:05:00'
        )
        
        # Act
        result = get_running_job()
        
        # Assert
        assert result is not None
        assert result['job_id'] == 'delta-123'
        assert result['kind'] == 'delta'
        assert result['status'] == 'running'
        assert result['processed'] == 50
        assert result['total'] == 100
        assert result['percent'] == 50
    
    @patch('app.services.sync_jobs.get_conn')
    def test_get_running_job_not_found(self, mock_get_conn):
        """Deve retornar None se não há job rodando."""
        # Arrange
        conn, cursor = Mock(), Mock()
        mock_get_conn.return_value = conn
        conn.__enter__ = Mock(return_value=conn)
        conn.__exit__ = Mock(return_value=None)
        conn.execute.return_value = cursor
        cursor.fetchone.return_value = None
        
        # Act
        result = get_running_job()
        
        # Assert
        assert result is None
    
    @patch('app.services.sync_jobs.get_conn')
    def test_get_running_job_with_kind_filter(self, mock_get_conn):
        """Deve filtrar por tipo de job."""
        # Arrange
        conn, cursor = Mock(), Mock()
        mock_get_conn.return_value = conn
        conn.__enter__ = Mock(return_value=conn)
        conn.__exit__ = Mock(return_value=None)
        conn.execute.return_value = cursor
        cursor.fetchone.return_value = None
        
        # Act
        get_running_job('backfill')
        
        # Assert
        call_args = conn.execute.call_args
        assert 'WHERE status = \'running\' AND kind = ?' in call_args[0][0]
        assert call_args[0][1] == ('backfill',)
    
    @patch('app.services.sync_jobs.get_conn')
    def test_get_last_success_job(self, mock_get_conn):
        """Deve retornar último job bem-sucedido."""
        # Arrange
        conn, cursor = Mock(), Mock()
        mock_get_conn.return_value = conn
        conn.__enter__ = Mock(return_value=conn)
        conn.__exit__ = Mock(return_value=None)
        conn.execute.return_value = cursor
        
        cursor.fetchone.return_value = (
            'delta-456', 'delta', 'success', 200, 200, 100,
            '2025-08-13T09:00:00', '2025-08-13T09:30:00'
        )
        
        # Act
        result = get_last_success_job()
        
        # Assert
        assert result is not None
        assert result['status'] == 'success'
        assert result['finished_at'] == '2025-08-13T09:30:00'
        
        # Verificar SQL
        call_args = conn.execute.call_args
        assert 'WHERE status = \'success\'' in call_args[0][0]
        assert 'ORDER BY finished_at DESC' in call_args[0][0]
    
    @patch('app.services.sync_jobs.get_conn')
    def test_has_running_job_true(self, mock_get_conn):
        """Deve retornar True se há job rodando."""
        # Arrange
        with patch('app.services.sync_jobs.get_running_job') as mock_get_running:
            mock_get_running.return_value = {'job_id': 'delta-123'}
            
            # Act
            result = has_running_job()
            
            # Assert
            assert result is True
    
    @patch('app.services.sync_jobs.get_conn')
    def test_has_running_job_false(self, mock_get_conn):
        """Deve retornar False se não há job rodando."""
        # Arrange
        with patch('app.services.sync_jobs.get_running_job') as mock_get_running:
            mock_get_running.return_value = None
            
            # Act
            result = has_running_job()
            
            # Assert
            assert result is False


class TestSyncJobsProgression:
    """Testes para progressão simulada de jobs."""
    
    @patch('app.services.sync_jobs.get_conn')
    def test_job_progression_simulation(self, mock_get_conn):
        """Simula progressão completa de um job com 3 lotes."""
        # Arrange
        conn = Mock()
        mock_get_conn.return_value = conn
        conn.__enter__ = Mock(return_value=conn)
        conn.__exit__ = Mock(return_value=None)
        
        # Act - Simular progressão
        # 1. Criar job
        job_id = create_job('delta')
        
        # 2. Atualizar progresso - Lote 1
        update_job(job_id, processed=25, total=100)
        
        # 3. Atualizar progresso - Lote 2  
        update_job(job_id, processed=50, total=100)
        
        # 4. Atualizar progresso - Lote 3
        update_job(job_id, processed=100, total=100)
        
        # 5. Finalizar job
        finish_job(job_id, 'success')
        
        # Assert - Verificar que foram feitas 5 chamadas
        assert conn.execute.call_count == 5
        
        # Verificar que foram chamadas as operações corretas
        call_args_list = [call[0] for call in conn.execute.call_args_list]
        
        # 1. Create job - deve conter INSERT
        assert 'INSERT INTO sync_jobs' in call_args_list[0][0]
        
        # 2-4. Update job - deve conter UPDATE com processed/total
        for i in range(1, 4):
            assert 'UPDATE sync_jobs' in call_args_list[i][0]
            assert 'processed = ?' in call_args_list[i][0]
            assert 'total = ?' in call_args_list[i][0]
        
        # 5. Finish job - deve conter UPDATE com status
        assert 'UPDATE sync_jobs' in call_args_list[4][0]
        assert 'status = ?' in call_args_list[4][0]
        assert 'finished_at' in call_args_list[4][0]


class TestSyncJobsCleanup:
    """Testes para limpeza de jobs antigos."""
    
    @patch('app.services.sync_jobs.get_conn')
    def test_cleanup_old_jobs(self, mock_get_conn):
        """Deve remover jobs antigos."""
        # Arrange
        conn = Mock()
        cursor = Mock()
        cursor.rowcount = 3
        conn.execute.return_value = cursor
        mock_get_conn.return_value = conn
        conn.__enter__ = Mock(return_value=conn)
        conn.__exit__ = Mock(return_value=None)
        
        # Act
        result = cleanup_old_jobs(days=7)
        
        # Assert
        assert result == 3
        conn.execute.assert_called_once()
        call_args = conn.execute.call_args
        assert 'DELETE FROM sync_jobs' in call_args[0][0]
        assert "status != 'running'" in call_args[0][0]
        assert "'-7 days'" in call_args[0][0]


class TestSyncJobsHistory:
    """Testes para histórico de jobs."""
    
    @patch('app.services.sync_jobs.get_conn')
    def test_get_job_history(self, mock_get_conn):
        """Deve retornar histórico de jobs."""
        # Arrange
        conn = Mock()
        cursor = Mock()
        conn.execute.return_value = cursor
        mock_get_conn.return_value = conn
        conn.__enter__ = Mock(return_value=conn)
        conn.__exit__ = Mock(return_value=None)
        
        # Mock de dados de histórico
        cursor.fetchall.return_value = [
            ('delta-123', 'delta', 'success', 100, 100, 100,
             '2025-08-13T10:00:00', '2025-08-13T10:30:00', '2025-08-13T10:30:00'),
            ('backfill-456', 'backfill', 'error', None, 50, None,
             '2025-08-13T09:00:00', None, '2025-08-13T09:15:00')
        ]
        
        # Act
        result = get_job_history(limit=5)
        
        # Assert
        assert len(result) == 2
        assert result[0]['job_id'] == 'delta-123'
        assert result[0]['status'] == 'success'
        assert result[1]['job_id'] == 'backfill-456'
        assert result[1]['status'] == 'error'
        
        # Verificar SQL
        call_args = conn.execute.call_args
        assert 'ORDER BY started_at DESC' in call_args[0][0]
        assert 'LIMIT ?' in call_args[0][0]
        assert call_args[0][1] == (5,)


class TestSyncJobsErrorHandling:
    """Testes para tratamento de erros."""
    
    @patch('app.services.sync_jobs.get_conn')
    @patch('app.services.sync_jobs.app_logger')
    def test_update_job_handles_exception(self, mock_logger, mock_get_conn):
        """Deve tratar exceções em update_job."""
        # Arrange
        conn = Mock()
        mock_get_conn.return_value = conn
        conn.__enter__ = Mock(return_value=conn)
        conn.__exit__ = Mock(side_effect=Exception("DB Error"))
        
        # Act - não deve lançar exceção
        update_job('job-123', 50, 100)
        
        # Assert
        mock_logger.log_error.assert_called_once()
    
    @patch('app.services.sync_jobs.get_conn')
    @patch('app.services.sync_jobs.app_logger')
    def test_get_running_job_handles_exception(self, mock_logger, mock_get_conn):
        """Deve tratar exceções em get_running_job."""
        # Arrange
        mock_get_conn.side_effect = Exception("Connection error")
        
        # Act
        result = get_running_job()
        
        # Assert
        assert result is None
        mock_logger.log_error.assert_called_once()
