# Sistema de Agendamento Automático (Scheduler)

## 📋 Visão Geral

O sistema de agendamento automático foi implementado para manter os dados frescos sem intervenção manual, executando sincronizações incrementais em intervalos regulares.

## 🏗️ Arquitetura

### Componentes Principais

1. **SyncScheduler** (`app/core/scheduler.py`)
   - Gerencia execução periódica usando APScheduler
   - BackgroundScheduler com timezone Brasil
   - Execuções únicas (max_instances=1) e coalescing

2. **UI Components** (`app/ui/components/scheduler_status.py`)
   - Status completo do scheduler
   - Controles manuais (start/stop/executar agora)
   - Badge compacto para sidebar

3. **Auto-Refresh Fallback** (`app/ui/components/autorefresh.py`)
   - Fallback usando st_autorefresh
   - Ativo quando scheduler não está rodando
   - Intervalos longos (30+ min) para páginas de alto tráfego

## ⚙️ Configuração

### secrets.toml
```toml
# Configurações do Scheduler Automático
SYNC_INTERVAL_MINUTES = 15
SCHEDULER_TIMEZONE = "America/Sao_Paulo"

# Configurações de Auto-Refresh (fallback)  
AUTOREFRESH_INTERVAL_MINUTES = 30
ENABLE_AUTOREFRESH_FALLBACK = true
```

### Variáveis de Ambiente (Alternativa)
```bash
SYNC_INTERVAL_MINUTES=15
SCHEDULER_TIMEZONE="America/Sao_Paulo"
```

## 🚀 Funcionalidades

### 1. Sincronização Automática
- **Intervalo:** Configurável (padrão: 15 minutos)
- **Execução:** `run_incremental_sync()` de forma assíncrona
- **Logging:** Completo com contexto e métricas de performance
- **Robustez:** Coalescing de execuções e prevenção de sobreposição

### 2. Session-Aware
- **Cache Resource:** Scheduler compartilhado entre sessões
- **Hibernação:** Para automaticamente quando não há sessões ativas
- **Inicialização:** Automática no startup da aplicação

### 3. UI Inteligente
- **Status em Tempo Real:** Última execução, próxima execução, resultado
- **Controles Manuais:** Reiniciar, executar agora, parar
- **Badges Compactos:** Status discreto em todas as páginas
- **Fallback Visual:** Auto-refresh opcional quando scheduler inativo

### 4. Monitoramento e Logs
- **Performance:** Duração das execuções
- **Erros:** Captura e logging de falhas
- **Estado:** Histórico de execuções e resultados
- **Debugging:** Logs estruturados com contexto completo

## 📊 Interface do Usuário

### Página Principal
```python
# Status completo com controles
from app.ui.components.scheduler_status import render_scheduler_status
render_scheduler_status(show_controls=True)
```

### Páginas Individuais (Sidebar)
```python
# Badge compacto na sidebar
from app.ui.components.scheduler_status import render_scheduler_badge
render_scheduler_badge()
```

### Auto-Refresh Inteligente
```python
# Sistema inteligente de refresh
from app.ui.components.autorefresh import render_smart_refresh
render_smart_refresh("page_name", high_traffic=True, interval_minutes=30)
```

## 🔧 API Programática

### Verificar Status
```python
from app.core.scheduler import get_scheduler_status

status = get_scheduler_status()
# {
#   "running": true,
#   "interval_minutes": 15,
#   "last_run": "2025-08-13T00:15:00",
#   "last_result": "sucesso", 
#   "next_run": "2025-08-13T00:30:00"
# }
```

### Inicialização Manual
```python
from app.core.scheduler import initialize_scheduler

scheduler = initialize_scheduler()
if scheduler:
    print("Scheduler iniciado com sucesso")
```

### Controle Direto
```python
from app.core.scheduler import get_scheduler

scheduler = get_scheduler()
scheduler.stop()  # Parar
scheduler.start()  # Iniciar
```

## 🎯 Cenários de Uso

### 1. Produção Normal
- Scheduler ativo em background
- Sincronizações automáticas a cada 15 minutos
- UI mostra status "🕐 Auto-sync ativo"
- Usuários podem forçar sync manual quando necessário

### 2. Desenvolvimento Local
- Scheduler funciona normalmente
- Intervalos menores para testes (5-10 min)
- Logs detalhados no console
- Controles manuais disponíveis

### 3. Streamlit Cloud/PaaS
- App pode hibernar - scheduler para automaticamente
- Auto-refresh como fallback em páginas críticas
- Reinicialização automática quando app acorda
- Configuração via secrets do cloud

### 4. Alto Tráfego
- Scheduler mantém dados frescos para todos os usuários
- Auto-refresh adicional em páginas específicas
- Intervalos otimizados para balancear frescor vs. performance
- Monitoring de execuções e ajuste dinâmico

## ⚠️ Considerações Importantes

### Limitações do Streamlit
- **Hibernação:** Apps podem dormir em clouds, parando o scheduler
- **Sessões:** Scheduler só roda enquanto há sessões ativas
- **Threads:** BackgroundScheduler usa threads daemon

### Performance
- **Coalescing:** Execuções atrasadas são combinadas
- **Max Instances:** Apenas 1 execução simultânea por recurso  
- **Cache:** Resultados cachados por TTL configurável
- **Rate Limiting:** Controle de frequência de requests para API

### Monitoramento
- **Health Checks:** Verificação de status via API
- **Alertas:** Logs de erro para falhas críticas
- **Métricas:** Duração, frequência, taxa de sucesso
- **Recovery:** Reinicialização automática em caso de falhas

## 🧪 Testes

### Validação Completa
```bash
python test_scheduler.py
```

### Testes Específicos
```python
# Testar inicialização
from app.core.scheduler import SyncScheduler
scheduler = SyncScheduler(interval_minutes=5)

# Testar componentes UI  
from app.ui.components.scheduler_status import render_scheduler_status

# Testar status
from app.core.scheduler import get_scheduler_status
status = get_scheduler_status()
```

## 📈 Resultados Esperados

### Antes (Manual)
- ❌ Dados desatualizados entre sessões
- ❌ Dependência de ação manual do usuário
- ❌ Performance inconsistente
- ❌ Experiência fragmentada

### Depois (Automático)
- ✅ Dados sempre frescos (15min max)
- ✅ Zero intervenção manual necessária
- ✅ Performance consistente para todos
- ✅ Experiência unificada e confiável

### Métricas de Sucesso
- **Frescor:** Dados nunca mais antigos que intervalo configurado
- **Disponibilidade:** 99%+ de execuções bem-sucedidas
- **Performance:** Sincronizações <30s em média
- **UX:** Feedback visual claro do status em tempo real
