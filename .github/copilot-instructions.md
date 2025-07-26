# Estas instruções se aplicam a TODO o repositório
applyTo: "**"
---

# Copilot Instructions · Indicadores-comg

> **Repositório** : https://github.com/Rafaelrdl/Indicadores-comg  
> **Stack base** : Python 3.12 · Streamlit ≥ 1.47 · Poetry · HTTPX (async) · Pydantic v2 · Plotly · Ruff + Black · Pytest  
> **Escopos fora do MVP** : banco SQL, Celery, CQRS/DDD completo, detecção de anomalias, 2FA, RBAC.

---

## 1 · Visão de alto nível

Indicadores-comg é um **dashboard multipage em Streamlit** que exibe KPIs de manutenção/engenharia clínica obtidos da **API Arkmeds**.  
A arquitetura segue quatro camadas bem-definidas:

core → data → services → ui/pages

markdown
Copiar
Editar

### 1.1 Pipeline principal

1. **Autenticação** · `ArkmedsAuth` fornece/renova JWT.  
2. **Ingestão** · `ArkmedsClient` (HTTPX - async) busca JSON paginado.  
3. **Validação** · Pydantic + helpers (`validation.py`).  
4. **Caching** · `smart_cache.py` com chaves sensíveis a filtros (Redis opcional).  
5. **Domínio** · Serviços calculam MTTR, MTBF, backlog, SLA.  
6. **UI** · Componentes reutilizáveis exibem métricas, gráficos, tabelas.

---

## 2 · Estrutura de diretórios (**fonte da verdade**)

app/
├─ core/ # Config, enums, exceptions, logging
│ ├─ config.py
│ ├─ constants.py
│ ├─ exceptions.py
│ └─ logging.py
├─ data/ # Modelos + cache
│ ├─ models/
│ └─ cache/
│ └─ smart_cache.py
├─ arkmeds_client/ # Integração externa
│ ├─ auth.py # ArkmedsAuth
│ ├─ client.py # ArkmedsClient (async)
│ └─ models.py # Schemas Pydantic
├─ services/ # Lógica de negócio/KPI
│ ├─ os_metrics.py
│ ├─ equip_metrics.py
│ └─ tech_metrics.py
├─ ui/ # Componentes e layouts Streamlit
│ ├─ components/
│ └─ layouts/
├─ pages/ # Arquivos multipage (prefixo numérico)
tests/ # Pytest suites

markdown
Copiar
Editar

---

## 3 · Diretrizes de implementação

### 3.1 Código & estilo

| Regra | Detalhe |
|-------|---------|
| **Formatação** | `ruff check --fix` + Black; *não* usar isort/mypy/bandit antes da F5. |
| **Tipagem** | 100 % type hints (`from __future__ import annotations`). |
| **Async** | Todo I/O externo → `async` + `httpx.AsyncClient` (*timeout* 15 s, 3 tentativas com back-off exponencial). |
| **Exceções** | Lançar subclasses de `app.core.exceptions.*` (nunca `Exception` cru). |
| **Logging** | A partir da F1 usar `structlog`. Inclua `request_id`, `org_id` no `extra`. |
| **Testes** | Criar/atualizar pytest; cobertura mínima 80 % para novos arquivos. Usar `pytest-asyncio` + `respx` p/ mocks HTTP. |

### 3.2 Padrões de código por domínio

#### Novo serviço de métrica (`services/…_metrics.py`)
1. Função pública `async def calculate_<nome>(df: pd.DataFrame, **kwargs) -> pd.DataFrame | dict`.
2. Validar `df` com helpers de `utils/validation.py`.
3. Decorar com `@smart_cache(ttl=<s>)` se custo > 3 s.
4. Documentar com docstring Google-style.
5. Testes unitários em `tests/services/`.

#### Novo endpoint Arkmeds
1. Método assíncrono em `arkmeds_client/client.py`.
2. Modelo Pydantic em `arkmeds_client/models.py`.
3. Adaptar para domínio (`services/`).
4. Cobrir via `respx` no teste de integração.

#### Nova página Streamlit
1. Arquivo `app/pages/4_<Slug>.py` (prefixo controla ordem).  
2. Usar `PageLayout` + componentes (`ui/`); *nunca* chamar API direto.  
3. Todas consultas virão de funções da camada `services/`.  
4. Título, ícone e descrição internacionais? Enviar via `PageLayout`.

---

## 4 · Roadmap (fases & tags)

| Fase | Janela | Metas chave | Tag de PR |
|------|--------|-------------|-----------|
| **F0** | Semana 0 | Kick-off, OKRs, setup do repo | `#roadmap:F0` |
| **F1** | Sem. 1-3 | Cliente async · Redis opcional · structlog | `#roadmap:F1` |
| **F2** | Sem. 4-6 | Pytest≥60 % · GH Action CI (lint + test) | `#roadmap:F2` |
| **F3** | Sem. 7-9 | Docker build · deploy manual · UI refactor | `#roadmap:F3` |
| **F4** | Sem. 10-14 | Multi-tenant infra · rate-limiter opt-in | `#roadmap:F4` |
| **F5** | Mês 4-6 | CI/CD full · pre-commit robusto · DDD light | `#roadmap:F5` |
| **F6** | Mês 6-9 | Histórico + Prophet/Anomaly Detection | `#roadmap:F6` |
| **F7** | Mês 9-12 | 2FA, RBAC, HA infra | `#roadmap:F7` |

> **Instruções ao Copilot**  
> *Quando sugerir código num PR, alinhe-o estritamente à fase indicada pela tag `#roadmap:`.*  
> Exemplo: pull-request marcado `#roadmap:F2` **não** deve adicionar CQRS ou configurações de Bandit.

---

## 5 · Seção “não gerar”

Copilot **deve evitar** propor neste estágio (até que as fases correspondentes cheguem):

* Banco relacional, migrations.  
* Celery/Redis‐queue, task schedulers.  
* Detecção de anomalias avançada.  
* CQRS, Aggregates, Event Sourcing.  
* Linters adicionais (isort, mypy estrito, bandit).  

Esses elementos só podem ser introduzidos quando a tag de roadmap correspondente estiver presente no PR.

---

## 6 · Instruções granulares via `applyTo`

Para instruções específicas de pasta/arquivo, criar arquivos em:

.github/instructions/<contexto>.instructions.md

yaml
Copiar
Editar

Com front-matter:

```yaml
---
applyTo: "app/services/os_metrics.py"
---

Descreva regra especial aqui…
Copilot deve respeitar essas instruções de escopo reduzido 
GitHub Docs
.

7 · Exemplos de commit/PR esperados
7.1 Feature pequena (F1)
bash
Copiar
Editar
feat: add async fetch_equipments   #roadmap:F1

* Added ArkmedsClient.fetch_equipments (async, retries, timeout 15 s)
* Added EquipmentSchema to arkmeds_client/models.py
* Added unit tests (100 % coverage) in tests/arkmeds
7.2 Refactor + testes (F2)
vbnet
Copiar
Editar
refactor: extract backlog calc to service   #roadmap:F2

* Moved backlog computation from page to services/os_metrics.py
* Added tests/services/test_backlog.py (92 % coverage)
* Updated ui components to call new service
8 · Glossário interno (nomes & abreviações)
Termo	Significado
OS	Ordem de Serviço (work order)
MTTR	Mean Time to Repair
MTBF	Mean Time Between Failures
SLA	Service Level Agreement
COMG	Centro Oftalmológico de Minas Gerais

Última revisão : 26 jul 2025