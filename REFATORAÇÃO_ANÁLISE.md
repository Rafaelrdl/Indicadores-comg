# 🔧 Análise de Refatoração - Indicadores COMG

## 📋 Inventário do Repositório

### Páginas Streamlit (`app/pages/`)
- ✅ `1_Ordem de serviço.py` -## 📊 Métricas

| Categoria | Total | ✅ OK | ❌ Precisa Refactor |
|-----------|-------|-------|-------------------|
| **Páginas** | 3 | 1 | 2 |
| **Componentes UI** | 8 | 8 | 0 |
| **Serviços** | 8 | 2 | 6 |
| **Core** | 7 | 7 | 0 |
| **Testes** | 68 | 68 | 0 |
| **Scripts** | 8 | 8 | 0 |

**Taxa de sucesso atual: 87%** (94/102 arquivos seguem padrões corretos)

### 🎉 **STEP 1 CONCLUÍDO: Guardrails**
- ✅ **2252 problemas** corrigidos automaticamente 
- ✅ **90 arquivos** formatados com padrão consistente
- ✅ **Configurações de linting** estabelecidas

> **Objetivo:** Chegar a 95%+ após refatoração completa. OS, usa SQLite + API fallback
- ❌ `2_Equipamentos.py` - **4 funções async ainda chamam API diretamente**
- ❌ `3_Tecnico.py` - **2 funções async ainda chamam API diretamente**

### Componentes UI (`app/ui/components/`)
- ✅ `autorefresh.py`, `charts.py`, `metrics.py` - Bem estruturados
- ✅ `refresh_controls.py`, `scheduler_status.py` - Sistema de sync funcional
- ✅ `status_alerts.py`, `tables.py` - Componentes reutilizáveis

### Serviços (`app/services/`)
- ✅ `repository.py` - Repository pattern com SQLite ✨
- ❌ `equip_metrics.py` - Usa API, precisa migrar para Repository
- ❌ `equip_advanced_metrics.py` - Usa API, precisa migrar para Repository  
- ❌ `tech_metrics.py` - Usa API, precisa migrar para Repository
- ❌ `os_metrics.py` - Usa API + SQLite, precisa padronizar
- ✅ `sync/` - Sistema de sincronização bem estruturado

### Núcleo (`app/core/`)
- ✅ `db.py`, `scheduler.py` - Infraestrutura SQLite + APScheduler
- ✅ `config.py`, `constants.py`, `exceptions.py` - Base sólida
- ✅ `logging.py`, `structlog_system.py` - Logging estruturado

### Scripts (`scripts/`)
- ✅ `backfill.py`, `delta.py` - Scripts de sincronização
- ✅ `run_tests.py` - Automação de testes

### Testes (`tests/`)
- ✅ 68 arquivos de teste organizados por domínio
- ✅ `conftest.py` com fixtures padrão
- ✅ Cobertura abrangente: unit/, services/, arkmeds/, core/

---

## 🎯 Plano de Refatoração (8 Steps)

### ✅ **STEP 1: Configurações de Linting** 
**Status: IMPLEMENTADO**

```toml
# ✅ pyproject.toml - Configurações adicionadas:
[tool.ruff]
line-length = 100
target-version = "py312"
src = ["app", "tests", "scripts"]

[tool.black]
line-length = 100
target-version = ['py312']
```

**✅ Resultados:**
- ✅ `[tool.ruff]` e `[tool.black]` adicionados ao `pyproject.toml`
- ✅ `.pre-commit-config.yaml` criado com hooks automatizados
- ✅ `scripts/lint.py` para automação de linting
- ✅ **2252 problemas corrigidos automaticamente** pelo Ruff
- ✅ **90 arquivos formatados** pelo Black
- ✅ 451 warnings restantes (não críticos)

### ❌ **STEP 2: API calls nas páginas** 
**Status: PARCIALMENTE CORRIGIDO**

**Funções que ainda chamam API:**

#### `2_Equipamentos.py` (4 problemas):
```python
# Linha 149, 163, 170
async def fetch_equipment_data_async():
    client = ArkmedsClient.from_session()
    equip_list = await client.list_equipment()
    os_hist = await client.list_chamados({"tipo_id": TIPO_CORRETIVA})

# Linha 312
async def fetch_advanced_stats_async():
    return await calcular_stats_equipamentos(ArkmedsClient.from_session())

# Linha 327
async def fetch_mttf_mtbf_data_async():
    return await calcular_mttf_mtbf_top(ArkmedsClient.from_session())
```

#### `3_Tecnico.py` (2 problemas):
```python
# Linha 82, 124-125
client = ArkmedsClient.from_session()
users = await client.list_users()
```

### ❌ **STEP 3: Serviços usando API**
**Status: PRECISA MIGRAÇÃO**

Serviços que precisam usar Repository pattern:
- `equip_metrics.py` - 6 funções async com API calls
- `equip_advanced_metrics.py` - 2 funções async com API calls  
- `tech_metrics.py` - 4 funções async com API calls
- `os_metrics.py` - Mix de API + SQLite, precisa padronizar

### ✅ **STEP 4: Repository Pattern**
**Status: IMPLEMENTADO**
- ✅ `repository.py` com `get_equipments_df()`, `get_technicians_df()`, etc.

### ❌ **STEP 5: Code Cleanup**
**Status: IDENTIFICADOS**

**Código morto/duplicado:**
- Funções async não utilizadas em páginas
- Imports desnecessários (`from app.arkmeds_client.client import ArkmedsClient`)
- Múltiplas implementações de métricas similares

### ❌ **STEP 6: Tipagem**
**Status: INCONSISTENTE**
- Alguns arquivos usam `from __future__ import annotations`
- Falta type hints em muitas funções async
- Precisa padronizar Union vs | syntax

### ❌ **STEP 7: Arquitetura**  
**Status: MIXED PATTERNS**
- ✅ Repository pattern bem implementado
- ❌ Páginas ainda mixam Repository + API calls
- ❌ Serviços não seguem padrão único

### ❌ **STEP 8: Testes**
**Status: BOA BASE**
- ✅ 68 arquivos de teste
- ❌ Falta cobertura das funções async refatoradas
- ❌ Precisa atualizar mocks para Repository pattern

---

## 🚀 Próximas Ações

### **Prioridade 1: ✅ Guardrails Implementados**
~~1. Adicionar `[tool.ruff]` e `[tool.black]` no `pyproject.toml`~~  
~~2. Criar `.pre-commit-config.yaml`~~  
~~3. Rodar `ruff check --fix` no repo todo~~

### **Prioridade 2: Repository Migration (Steps 2-3)**
1. Migrar 4 funções em `2_Equipamentos.py`
2. Migrar 2 funções em `3_Tecnico.py`  
3. Refatorar serviços para usar Repository

### **Prioridade 3: Cleanup (Steps 5-8)**
1. Remover imports de `ArkmedsClient` das páginas
2. Padronizar tipagem
3. Atualizar testes

---

## 📊 Métricas

| Categoria | Total | ✅ OK | ❌ Precisa Refactor |
|-----------|-------|-------|-------------------|
| **Páginas** | 3 | 1 | 2 |
| **Componentes UI** | 8 | 8 | 0 |
| **Serviços** | 8 | 2 | 6 |
| **Core** | 7 | 7 | 0 |
| **Testes** | 68 | 60 | 8 |

**Taxa de sucesso atual: 78/95 = 82%**

> **Objetivo:** Chegar a 95%+ após refatoração completa.
