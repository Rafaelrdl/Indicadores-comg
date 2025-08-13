# Dashboard Ar### ✨ Características Principais
- **🕐 Sincronização Automática**: Agendamento periódico session-aware (15min)
- **📊 Indicadores de Progresso**: Barras de progresso em tempo real com persistência
- **🚀 Startup Sync**: Sincronização automática não-bloqueante ao iniciar o app
- **⚡ Performance 99%+ Melhor**: Leitura local SQLite### 🔄 Tipos de Sincronização

#### 1. Startup Sync (Automática)
- **Quando**: Automaticamente ao abrir o app
- **Como**: Verifica se dados estão desatualizados (1h padrão)
- **Progresso**: Barra de progresso na tela principal
- **Performance**: ~10-30 segundos (apenas se necessário)
- **Configuração**: `ENABLE_STARTUP_SYNC = true` em `secrets.toml`

#### 2. Backfill Completo
- **Quando usar**: Primeira execução ou reset completo
- **Como**: Busca todos os dados da API
- **Progresso**: Indicadores detalhados por recurso
- **Performance**: ~2-5 minutos dependendo do volume
- **Comando**: `poetry run python -m scripts.backfill`

#### 3. Sincronização Incremental (Delta)
- **Quando usar**: Atualizações regulares (padrão do scheduler)
- **Como**: Apenas dados novos/modificados desde última sync
- **Progresso**: Barra de progresso em tempo real
- **Performance**: ~10-30 segundos
- **Comando**: `poetry run python -m scripts.delta`ta
- **🔄 Sistema Inteligente**: Backfill completo + sincronização incremental
- **🎛️ Controles Interativos**: UI para gerenciar dados e status
- **📊 Métricas Completas**: KPIs, análises e visualizações avançadas
- **🏗️ Arquitetura Robusta**: Modular, escalável e bem testada Indicadores COMG

![CI](https://github.com/Rafaelrdl/Indicadores-comg/actions/workflows/ci.yml/badge.svg)
![CD](https://github.com/Rafaelrdl/Indicadores-comg/actions/workflows/cd.yml/badge.svg)
![LOC](https://img.shields.io/tokei/lines/github/Rafaelrdl/Indicadores-comg)
![License](https://img.shields.io/github/license/Rafaelrdl/Indicadores-comg)

![Preview](docs/home_page.png)

## 📋 Visão Geral

Dashboard multipage em Streamlit para consolidar indicadores da plataforma Arkmeds.
Sistema completo com **sincronização automática**, cache inteligente e performance otimizada.

### ✨ Características Principais
- **🕐 Sincronização Automática**: Agendamento periódico session-aware (15min)
- **⚡ Performance 99%+ Melhor**: Leitura local SQLite vs. API remota
- **🔄 Sistema Inteligente**: Backfill completo + sincronização incremental
- **�️ Controles Interativos**: UI para gerenciar dados e status
- **📊 Métricas Completas**: KPIs, análises e visualizações avançadas
- **🏗️ Arquitetura Robusta**: Modular, escalável e bem testada

## 🏗️ Arquitetura do Sistema

```
├── 📱 app/                     # Aplicação principal
│   ├── core/                   # Infraestrutura central
│   │   ├── scheduler.py        # 🕐 Sistema de agendamento automático
│   │   ├── startup.py          # 🚀 Sincronização automática na inicialização
│   │   └── db.py              # 🗄️ Banco SQLite + migrações
│   ├── services/sync/          # 🔄 Sistema de sincronização
│   │   ├── ingest.py          # 📥 Backfill completo
│   │   └── delta.py           # 📊 Sincronização incremental
│   ├── services/               # 🛠️ Serviços de negócio
│   │   └── sync_jobs.py       # 📊 Rastreamento de progresso de jobs
│   ├── ui/components/          # 🎛️ Componentes interativos
│   │   ├── refresh_controls.py # 🔄 Controles de atualização
│   │   └── scheduler_status.py # 📊 Status do scheduler
│   ├── pages/                  # 📄 Páginas do dashboard
│   └── arkmeds_client/         # 🌐 Cliente API
├── � scripts/                 # 🚀 CLI para operações
├── 🧪 tests/                   # ✅ Testes automatizados
└── 📖 docs/                    # 📚 Documentação completa
```

## 🚀 Quick Start

### 1. Configuração Inicial

```bash
# Clone e instale
git clone https://github.com/Rafaelrdl/Indicadores-comg.git
cd Indicadores-comg
poetry install

# Configure credenciais
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edite o arquivo com suas credenciais da API
```

### 2. Configuração do secrets.toml

Edite `.streamlit/secrets.toml`:

```toml
[arkmeds]
email = "seu_email@exemplo.com"
password = "sua_senha"
base_url = "https://comg.arkmeds.com"

# Sistema de Agendamento Automático
SYNC_INTERVAL_MINUTES = 15          # Intervalo de sincronização (15min padrão)
SCHEDULER_TIMEZONE = "America/Sao_Paulo"

# Startup Sync - Sincronização Automática na Inicialização
ENABLE_STARTUP_SYNC = true          # Ativa sync automática ao abrir app
STARTUP_SYNC_CHECK_HOURS = 1        # Verifica se sync é necessária (1h padrão)

# Progress UI - Interface de Progresso
PROGRESS_UI_REFRESH_MS = 2000       # Atualização da barra de progresso (2s)

# Auto-Refresh Fallback (páginas de alto tráfego)
AUTOREFRESH_INTERVAL_MINUTES = 30   # Fallback quando scheduler inativo
ENABLE_AUTOREFRESH_FALLBACK = true
```

### 3. Primeira Sincronização

```bash
# Sincronização completa inicial (CLI)
poetry run python -m scripts.backfill

# Ou sincronização incremental
poetry run python -m scripts.delta
```

### 4. Executar Dashboard

```bash
# Iniciar aplicação (scheduler automático incluído)
poetry run streamlit run app/main.py
```

## 🔧 Comandos CLI

### Backfill Completo
```bash
# Sincronização completa de todos os recursos
poetry run python -m scripts.backfill

# Recursos específicos
poetry run python -m scripts.backfill --resources orders,equipments

# Modo dry-run (apenas mostrar o que seria feito)
poetry run python -m scripts.backfill --dry-run

# Com força (sobrescrever dados existentes)
poetry run python -m scripts.backfill --force --verbose
```

### Sincronização Incremental
```bash
# Sincronização apenas de dados novos/modificados
poetry run python -m scripts.delta

# Verificar apenas se sync é necessário
poetry run python -m scripts.delta --check-only

# Forçar sincronização completa
poetry run python -m scripts.delta --force-full

# Recursos específicos com intervalo customizado
poetry run python -m scripts.delta --resources orders --min-interval 10
```

## 📊 Sistema de Indicadores de Progresso

O dashboard implementa um sistema completo de rastreamento de progresso para todas as operações de sincronização, fornecendo feedback visual em tempo real.

### ✨ Funcionalidades

#### 🚀 Startup Sync
- **Sincronização Automática**: Executa automaticamente ao abrir o app
- **Não-Bloqueante**: Roda em background sem travar a interface
- **Cache Inteligente**: Evita sincronizações desnecessárias
- **Sobreposição Zero**: Previne múltiplas execuções simultâneas

#### 📊 Progress UI
- **Barras de Progresso**: Visualização em tempo real do progresso
- **Persistência**: Estado salvo no SQLite durante execução
- **Auto-Refresh**: Interface atualiza automaticamente (2s padrão)
- **Status Detalhado**: Mostra tipo, progresso, e tempo decorrido

#### 🗄️ Job Management
- **Rastreamento Completo**: Histórico de todos os jobs executados
- **Estados**: `running`, `success`, `error`, `cancelled`
- **Métricas**: Tempo de execução, itens processados, percentual
- **Limpeza Automática**: Remove jobs antigos automaticamente

### 🎛️ Interface Visual

#### Tela Principal
```
🔄 Sincronização em Andamento
━━━━━━━━━━━━━━━━━━━━ 65% (130/200)
📈 Delta Sync | ⏱️ 00:02:15
```

#### Durante Startup Sync
```
🚀 Sincronização Inicial...
━━━━━━━━━━░░░░░░░░░░ 50%
🔄 Verificando dados recentes...
```

### ⚙️ Configurações

```toml
# .streamlit/secrets.toml
[arkmeds]
# Startup Sync
ENABLE_STARTUP_SYNC = true          # Ativar sync automática
STARTUP_SYNC_CHECK_HOURS = 1        # Verificar necessidade (1h)

# Progress UI  
PROGRESS_UI_REFRESH_MS = 2000       # Refresh da barra (2s)
```

### 📡 Fluxo de Execução

1. **App Start**: `ensure_startup_sync()` verifica necessidade
2. **Job Creation**: Cria registro no SQLite com status `running`
3. **Progress Updates**: Atualiza `processed/total` em tempo real
4. **UI Refresh**: Auto-refresh mostra progresso na tela
5. **Job Completion**: Finaliza com status `success/error`

### 🔧 API de Jobs

```python
from app.services.sync_jobs import (
    create_job,      # Criar novo job
    update_job,      # Atualizar progresso
    finish_job,      # Finalizar job
    get_running_job, # Job em execução
    has_running_job  # Verificar se há job rodando
)

# Exemplo de uso
job_id = create_job('delta')
update_job(job_id, processed=50, total=100)
finish_job(job_id, 'success')
```

### 🧪 Testes

```bash
# Testar sistema de progresso
poetry run python -m pytest tests/test_sync_progress.py -v

# Testar startup sync
poetry run python -m pytest tests/test_startup_sync.py -v

# Simular job completo
poetry run python -c "
from app.services.sync_jobs import create_job, update_job, finish_job
import time
job_id = create_job('delta')
for i in [25, 50, 75, 100]:
    update_job(job_id, i, 100)
    time.sleep(1)
finish_job(job_id, 'success')
"
```

## 🧪 Desenvolvimento e Testes

### 🧪 Executar Testes
```bash
# Testes principais
poetry run python -m pytest tests/test_sqlite_refactor.py -v
poetry run python -m pytest tests/test_refresh_controls.py -v
poetry run python -m pytest tests/test_basic_logging.py -v

# Testes do sistema de progresso
poetry run python -m pytest tests/test_sync_progress.py -v
poetry run python -m pytest tests/test_startup_sync.py -v

# Teste do scheduler
poetry run python test_scheduler.py

# Validação completa
poetry run python final_test.py
```

### Estrutura de Testes
- **🧪 Testes Unitários**: Validação de componentes individuais
- **🔗 Testes de Integração**: Verificação de sistema completo
- **📊 Testes de Performance**: Benchmarks e métricas
- **🤖 Testes do Scheduler**: Validação do agendamento automático

## 📚 Documentação Adicional

- **[Sistema de Scheduler](docs/scheduler-system.md)**: Documentação detalhada do agendamento
- **[Refatoração SQLite](documentation/REFACTORING_SUMMARY.md)**: Detalhes técnicos da migração
- **[Correções Implementadas](documentation/CORREÇÕES_REALIZADAS.md)**: Histórico de correções

## 🛠️ Scripts Utilitários

### Manutenção do Banco
```bash
# Inicializar/migrar banco
poetry run python -c "from app.core.db import init_database; init_database()"

# Estatísticas do banco
poetry run python -c "from app.services.repository import get_database_stats; import json; print(json.dumps(get_database_stats(), indent=2, default=str))"
```

### Debug e Monitoramento
```bash
# Verificar status do scheduler
poetry run python -c "from app.core.scheduler import get_scheduler_status; import json; print(json.dumps(get_scheduler_status(), indent=2, default=str))"

# Logs em tempo real
poetry run streamlit run app/main.py --logger.level debug
```

## 🤝 Contribuição

### Setup de Desenvolvimento
```bash
# Fork e clone
git clone https://github.com/SEU_USUARIO/Indicadores-comg.git
cd Indicadores-comg

# Instalar dependências de desenvolvimento
poetry install --with dev

# Pre-commit hooks
poetry run pre-commit install

# Executar testes antes de commit
poetry run python final_test.py
```

### Padrões de Código
- **Formatação**: Black + Ruff
- **Tipagem**: Type hints obrigatórios
- **Testes**: Cobertura mínima 80%
- **Documentação**: Docstrings Google-style

## � Licença

Este projeto está licenciado sob a [MIT License](LICENSE).

## 🆘 Suporte

### FAQ

**Q: O scheduler não está rodando?**
A: Verifique se há sessões ativas no Streamlit e se as configurações estão corretas em `secrets.toml`.

**Q: Dados não estão atualizando?**
A: Use `poetry run python -m scripts.delta --check-only` para verificar se sincronização é necessária.

**Q: Como configurar intervalo personalizado?**
A: Edite `SYNC_INTERVAL_MINUTES` em `secrets.toml` e reinicie a aplicação.

**Q: Performance lenta na primeira execução?**
A: Execute `poetry run python -m scripts.backfill` para sincronização inicial completa.

### Contato
- **GitHub Issues**: [Reportar Problemas](https://github.com/Rafaelrdl/Indicadores-comg/issues)
- **Discussões**: [GitHub Discussions](https://github.com/Rafaelrdl/Indicadores-comg/discussions)

---

**🎉 Dashboard completo com sincronização automática e performance otimizada!**
- **Session-Aware**: Roda apenas com sessões ativas
- **Thread-Safe**: BackgroundScheduler com coalescing
- **Monitoramento**: Logs estruturados e métricas em tempo real

### � Tipos de Sincronização

#### 1. Backfill Completo
- **Quando usar**: Primeira execução ou reset completo
- **Como**: Busca todos os dados da API
- **Performance**: ~2-5 minutos dependendo do volume
- **Comando**: `poetry run python -m scripts.backfill`

#### 2. Sincronização Incremental (Delta)
- **Quando usar**: Atualizações regulares (padrão do scheduler)
- **Como**: Apenas dados novos/modificados desde última sync
- **Performance**: ~10-30 segundos
- **Comando**: `poetry run python -m scripts.delta`

### 🎛️ Controles de Interface

#### Página Principal
- **Status completo** do scheduler com controles
- **Métricas** de sincronização em tempo real
- **Controles manuais**: start/stop/executar agora

#### Páginas Individuais
- **Badge discreto** na sidebar mostrando status
- **Botões de refresh** para sincronização manual
- **Status dos dados** com última atualização

## 🌐 Deployment

### Streamlit Cloud
```toml
# .streamlit/secrets.toml (no painel do Streamlit Cloud)
[arkmeds]
email = "EMAIL_DA_API"
password = "SENHA_DA_API"
base_url = "https://comg.arkmeds.com"

SYNC_INTERVAL_MINUTES = 30  # Intervalo maior para cloud
ENABLE_AUTOREFRESH_FALLBACK = true
```

**⚠️ Limitações em Hosting Gratuito:**
- Apps hibernam após inatividade → scheduler para automaticamente
- **Solução**: Auto-refresh opcional ativado automaticamente
- **Recomendação**: Intervalos maiores (30+ min) para reduzir consumo

### Docker
```bash
# Build e run com Docker
docker build -t indicadores-comg .
docker run -p 8501:8501 indicadores-comg
```

### Variáveis de Ambiente (Alternativa)
```bash
# Para containers ou CI/CD
export ARKMEDS_EMAIL="seu_email@exemplo.com"
export ARKMEDS_PASSWORD="sua_senha"
export SYNC_INTERVAL_MINUTES=15
export SCHEDULER_TIMEZONE="America/Sao_Paulo"
```

## 📈 Performance e Otimizações

### Antes vs. Depois
- **Carregamento de Página**: 8-12s → <0.5s (**95%+ melhoria**)
- **Atualização de Dados**: Manual → Automática (15min)
- **Experiência do Usuário**: Inconsistente → Sempre fresh
- **Carga no Servidor**: Alta → Mínima (cache local)

### Benchmarks
```bash
# Teste de performance
poetry run python final_test.py

# Métricas de sincronização
poetry run python -m scripts.delta --verbose
```

# 2. Edite as configurações
# .env ou .streamlit/secrets.toml:
# [arkmeds]
# base_url = "https://comg.arkmeds.com"
# (opcional) token = "seu_jwt_token_aqui"

# 3. Instale dependências e execute
poetry install --no-dev
poetry run streamlit run app/main.py
```

### 🖥️ Acesso Local
Após iniciar, acesse: `http://localhost:8501`

## 🛠️ Comandos Úteis

```bash
# Desenvolvimento
poetry install                          # Instala todas as dependências
poetry run streamlit run app/main.py    # Inicia o dashboard
poetry run python scripts/run_tests.py  # Executa testes

# Produção
poetry install --no-dev                 # Só dependências de produção
poetry run streamlit run app/main.py --server.port 8080
```

## 📚 Documentação

- **[📖 Documentação Técnica](./documentation/)** - Arquitetura e desenvolvimento
- **[🎨 Assets](./assets/)** - Recursos visuais e logos
- **[📊 Dados](./data/)** - Estruturas de dados e investigações
- **[🧪 Testes](./tests/)** - Estratégia e cobertura de testes

## 🎯 Funcionalidades

### 📊 Dashboards Disponíveis
1. **Ordens de Serviço** - Análise de chamados e SLA
2. **Equipamentos** - MTTR, MTBF e disponibilidade
3. **Técnicos** - Performance e produtividade da equipe

### 🔧 Componentes Principais
- **Métricas Interativas** - KPIs com visualização dinâmica
- **Tabelas Avançadas** - Filtros, paginação e exportação
- **Gráficos Responsivos** - Plotly integrado
- **Cache Inteligente** - Performance otimizada

## 📋 Boas Práticas

### 🗂️ Organização de Código
- Nomes de arquivo em `app/pages/` com caracteres ASCII
- Cada página define `st.set_page_config()`
- Componentes reutilizáveis em `app/ui/components/`
- Lógica de negócio isolada em `app/services/`

### 🔒 Segurança
- Nunca commite credenciais no código
- Use `.env` e `secrets.toml` para configurações
- Valide dados de entrada da API
- Mantenha dependências atualizadas

## 🤝 Contribuindo

1. **Fork** o repositório
2. **Crie** uma branch: `git checkout -b feature/nova-funcionalidade`
3. **Commit** suas mudanças: `git commit -m 'Adiciona nova funcionalidade'`
4. **Push** para a branch: `git push origin feature/nova-funcionalidade`
5. **Abra** um Pull Request

### 📝 Padrões de Commit
- `feat:` - Nova funcionalidade
- `fix:` - Correção de bug
- `docs:` - Documentação
- `style:` - Formatação
- `refactor:` - Refatoração
- `test:` - Testes

## 📄 Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE).

## Contato / Licenca

Projeto sob a [MIT License](LICENSE). Dúvidas abra uma issue.
<!-- Random comment for PR test -->
