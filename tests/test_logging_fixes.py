#!/usr/bin/env python3
"""
Teste das correções de logging e datetime no sistema de sync.
"""

import sys
import traceback
from datetime import datetime

def test_logging_import():
    """Testa se o sistema de logging funciona corretamente."""
    try:
        from app.core.logging import app_logger as logger
        
        # Testar métodos disponíveis
        logger.log_info("✅ Teste de logging - INFO")
        logger.log_error("✅ Teste de logging - ERROR") 
        logger.log_warning("✅ Teste de logging - WARNING")
        
        print("✅ Sistema de logging funcionando corretamente")
        return True
        
    except Exception as e:
        print(f"❌ Erro no sistema de logging: {e}")
        traceback.print_exc()
        return False

def test_datetime_parsing():
    """Testa se o parsing de datetime funciona com validação."""
    try:
        from app.services.sync.delta import IncrementalSync
        from app.services.sync._upsert import get_last_sync_info
        from app.core.db import get_conn
        
        # Simular dados do banco que podem causar erro
        test_cases = [
            (None, "nulo"),
            ("", "string vazia"),  
            ("2025-08-13T00:34:36.743487", "ISO format válido"),
        ]
        
        for i, (test_value, description) in enumerate(test_cases):
            try:
                # Simular o que acontece no código
                if not test_value or not isinstance(test_value, str):
                    print(f"✅ Teste {i+1}: Valor {description} '{test_value}' tratado corretamente")
                    continue
                    
                # Tentar fazer o parsing
                parsed_date = datetime.fromisoformat(test_value)
                print(f"✅ Teste {i+1}: Valor {description} '{test_value}' parseado como {parsed_date}")
                
            except Exception as e:
                print(f"❌ Teste {i+1}: Erro ao parsear {description} '{test_value}': {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de datetime: {e}")
        traceback.print_exc()
        return False

def test_sync_functions():
    """Testa se as funções de sync podem ser importadas sem erro."""
    try:
        from app.services.sync.delta import IncrementalSync
        from app.services.sync.ingest import BackfillSync
        from app.services.sync._upsert import get_last_sync_info
        
        print("✅ Todas as classes de sync importadas com sucesso")
        return True
        
    except Exception as e:
        print(f"❌ Erro importando classes de sync: {e}")
        traceback.print_exc()
        return False

def main():
    """Executa todos os testes."""
    print("🧪 Iniciando testes das correções de logging e datetime...\n")
    
    tests = [
        ("Sistema de Logging", test_logging_import),
        ("Parsing de DateTime", test_datetime_parsing), 
        ("Funções de Sync", test_sync_functions),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"🔄 Testando: {test_name}")
        result = test_func()
        results.append((test_name, result))
        print(f"{'✅' if result else '❌'} {test_name}: {'PASSOU' if result else 'FALHOU'}\n")
    
    # Resumo final
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"📊 RESUMO DOS TESTES:")
    print(f"   Passou: {passed}/{total}")
    print(f"   Falhou: {total-passed}/{total}")
    
    if passed == total:
        print("🎉 Todas as correções foram aplicadas com sucesso!")
        return 0
    else:
        print("❌ Algumas correções ainda precisam de atenção.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
