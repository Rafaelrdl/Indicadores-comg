# Testes - Indicadores COMG

Esta pasta contém todos os testes do projeto Indicadores-comg.

## Estrutura dos Testes

### Testes por Módulo
- `arkmeds/` - Testes do cliente Arkmeds
- `core/` - Testes do core do sistema
- `services/` - Testes dos serviços
- `unit/` - Testes unitários
- `temp/` - Testes temporários

### Testes de Integração
- `test_full_integration.py` - Testes de integração completos
- `test_integration_final.py` - Testes de integração finais
- `test_simple_sync.py` - Testes de sincronização simples

### Testes de Funcionalidades
- `test_cli.py` - Testes da interface de linha de comando
- `test_pagination.py` - Testes de paginação
- `test_scheduler.py` - Testes do agendador
- `test_logging_fixes.py` - Testes das correções de logging
- `test_list_chamados_fix.py` - Testes de correção da listagem de chamados

### Testes de Database
- `test_database.py` - Testes gerais de banco de dados
- `test_sqlite_refactor.py` - Testes da refatoração SQLite
- `test_models_chamado.py` - Testes dos modelos de chamado

### Testes de Sistema
- `test_startup_sync.py` - Testes de sincronização na inicialização
- `test_sync_system.py` - Testes do sistema de sincronização
- `test_sync_progress.py` - Testes do progresso de sincronização
- `test_basic_logging.py` - Testes básicos de logging

### Testes de UI
- `test_configuracoes_page.py` - Testes da página de configurações
- `test_refresh_controls.py` - Testes dos controles de atualização

### Performance e Investigação
- `benchmark_performance.py` - Benchmarks de performance
- `investigate_sqlite.py` - Investigação SQLite
- `final_test.py` - Teste final

### Arquivos de Saída
- `test_error.txt` - Log de erros dos testes
- `test_output.txt` - Saída dos testes

## Configuração
- `conftest.py` - Configuração global do pytest
- `pytest.ini` - Configuração do pytest (na raiz do projeto)

## Execução dos Testes

```bash
# Executar todos os testes
pytest

# Executar testes específicos
pytest tests/test_database.py

# Executar com coverage
pytest --cov=app

# Executar testes de integração
pytest tests/test_*integration*.py
```
