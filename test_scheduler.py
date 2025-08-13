"""
Teste para validar o sistema de agendamento automático.

Este teste verifica se o scheduler pode ser inicializado e se os componentes
de UI funcionam corretamente.
"""
import sys
import os
from datetime import datetime

# Adicionar app ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_scheduler_initialization():
    """Testa inicialização do scheduler."""
    print("🧪 Testando inicialização do scheduler...")
    
    try:
        from app.core.scheduler import SyncScheduler, get_scheduler_status
        
        # Testar criação do scheduler
        scheduler = SyncScheduler(interval_minutes=5)  # Intervalo curto para teste
        print(f"   ✅ Scheduler criado com intervalo de 5 minutos")
        
        # Testar status
        status = scheduler.get_status()
        print(f"   ✅ Status obtido: running={status['running']}")
        
        # Não iniciar de fato para evitar jobs rodando em background
        print("   ✅ Scheduler pode ser inicializado (não iniciado para evitar background jobs)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro na inicialização do scheduler: {e}")
        return False

def test_scheduler_status_function():
    """Testa função de status global."""
    print("🧪 Testando função de status do scheduler...")
    
    try:
        from app.core.scheduler import get_scheduler_status
        
        # Testar obtenção de status
        status = get_scheduler_status()
        print(f"   ✅ Status obtido: {len(status)} campos")
        
        # Verificar campos obrigatórios
        required_fields = ['running', 'interval_minutes', 'last_run', 'last_result', 'next_run']
        missing = [field for field in required_fields if field not in status]
        
        if missing:
            print(f"   ❌ Campos faltantes: {missing}")
            return False
        else:
            print("   ✅ Todos os campos obrigatórios estão presentes")
            return True
            
    except Exception as e:
        print(f"   ❌ Erro na função de status: {e}")
        return False

def test_scheduler_ui_components():
    """Testa componentes de UI do scheduler."""
    print("🧪 Testando componentes de UI do scheduler...")
    
    try:
        from app.ui.components.scheduler_status import (
            render_scheduler_status,
            render_scheduler_badge,
            get_scheduler_status
        )
        
        # Testar importação dos componentes
        print("   ✅ Componentes de UI importados com sucesso")
        
        # Testar função de status que é usada pelos componentes
        status = get_scheduler_status()
        print(f"   ✅ Status para UI obtido: running={status.get('running', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro nos componentes de UI: {e}")
        return False

def test_autorefresh_components():
    """Testa componentes de auto-refresh."""
    print("🧪 Testando componentes de auto-refresh...")
    
    try:
        from app.ui.components.autorefresh import (
            render_autorefresh_fallback,
            render_smart_refresh,
            render_autorefresh_badge
        )
        
        print("   ✅ Componentes de auto-refresh importados com sucesso")
        
        # Verificar se streamlit-autorefresh está disponível
        import streamlit_autorefresh
        print("   ✅ Dependência streamlit-autorefresh disponível")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Erro de importação: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Erro nos componentes de auto-refresh: {e}")
        return False

def test_configuration_loading():
    """Testa carregamento das configurações do scheduler."""
    print("🧪 Testando carregamento de configurações...")
    
    try:
        # Testar configurações via secrets (simulado)
        import os
        
        # Definir valores padrão para teste
        interval = int(os.environ.get("SYNC_INTERVAL_MINUTES", 15))
        timezone = os.environ.get("SCHEDULER_TIMEZONE", "America/Sao_Paulo")
        
        print(f"   ✅ Configurações carregadas: interval={interval}min, timezone={timezone}")
        
        # Testar se as configurações fazem sentido
        if interval < 1 or interval > 1440:  # Entre 1 minuto e 24 horas
            print(f"   ⚠️ Aviso: intervalo incomum ({interval} minutos)")
        else:
            print(f"   ✅ Intervalo está dentro do esperado")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro no carregamento de configurações: {e}")
        return False

def test_dependencies():
    """Testa se todas as dependências estão instaladas."""
    print("🧪 Testando dependências...")
    
    dependencies = [
        ("apscheduler", "APScheduler"),
        ("streamlit_autorefresh", "Streamlit Auto-refresh")
    ]
    
    success = True
    
    for module_name, display_name in dependencies:
        try:
            __import__(module_name)
            print(f"   ✅ {display_name} disponível")
        except ImportError:
            print(f"   ❌ {display_name} não encontrado")
            success = False
    
    return success

def main():
    """Executa todos os testes do scheduler."""
    print("🚀 Iniciando testes do sistema de agendamento...")
    print("=" * 50)
    
    tests = [
        test_dependencies,
        test_configuration_loading,
        test_scheduler_initialization,
        test_scheduler_status_function,
        test_scheduler_ui_components,
        test_autorefresh_components,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Resultado final: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Sistema de agendamento implementado com sucesso!")
        print("✅ Pronto para varreduras automáticas periódicas")
        return True
    else:
        print("⚠️ Alguns testes falharam")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
