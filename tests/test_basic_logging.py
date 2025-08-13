"""
Teste simplificado para identificar problemas de logging.
"""
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_basic_imports():
    print("🔍 Teste básico de imports e logging")
    
    try:
        from app.core.logging import app_logger
        print("✅ app_logger importado")
        
        # Testar método correto
        app_logger.log_info("Teste de logging")
        print("✅ log_info funciona")
        
        app_logger.log_error("Teste de erro")
        print("✅ log_error funciona")
        
    except Exception as e:
        print(f"❌ Erro no logging: {e}")
        return False
    
    try:
        from app.ui.components.status_alerts import check_global_status
        print("✅ check_global_status importado")
        
        # Testar função
        result = check_global_status(['orders'])
        print(f"✅ Status retornado: {len(result)} campos")
        
    except Exception as e:
        print(f"❌ Erro em check_global_status: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_basic_imports()
    print(f"\n🏁 Resultado: {'SUCESSO' if success else 'FALHA'}")
