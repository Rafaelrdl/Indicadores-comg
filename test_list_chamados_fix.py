#!/usr/bin/env python3
"""
Teste das correções do erro 'str' object has no attribute 'list_chamados'.
"""

def test_run_incremental_sync_signature():
    """Testa se a função run_incremental_sync tem a assinatura correta."""
    try:
        from app.services.sync.delta import run_incremental_sync
        import inspect
        
        # Obter assinatura da função
        sig = inspect.signature(run_incremental_sync)
        params = list(sig.parameters.keys())
        
        print(f"✅ Função encontrada: run_incremental_sync")
        print(f"📋 Parâmetros: {params}")
        
        # Verificar se client é o primeiro parâmetro
        if params and params[0] == 'client':
            print(f"✅ Primeiro parâmetro é 'client' - CORRETO")
            return True
        else:
            print(f"❌ Primeiro parâmetro deveria ser 'client', mas é '{params[0] if params else 'nenhum'}'")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao importar função: {e}")
        return False

def test_incremental_sync_class():
    """Testa se a classe IncrementalSync está funcionando."""
    try:
        from app.services.sync.delta import IncrementalSync
        from app.arkmeds_client.client import ArkmedsClient
        
        print(f"✅ Classe IncrementalSync importada com sucesso")
        
        # Verificar se pode ser instanciada (sem realmente instanciar)
        import inspect
        init_sig = inspect.signature(IncrementalSync.__init__)
        init_params = list(init_sig.parameters.keys())
        
        print(f"📋 Parâmetros do __init__: {init_params}")
        
        if 'client' in init_params:
            print(f"✅ Classe espera parâmetro 'client' - CORRETO")
            return True
        else:
            print(f"❌ Classe não tem parâmetro 'client'")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar classe: {e}")
        return False

def test_arkmeds_client_methods():
    """Verifica se ArkmedsClient tem os métodos necessários."""
    try:
        from app.arkmeds_client.client import ArkmedsClient
        
        # Métodos esperados
        expected_methods = ['list_chamados']
        
        for method in expected_methods:
            if hasattr(ArkmedsClient, method):
                print(f"✅ Método {method} encontrado em ArkmedsClient")
            else:
                print(f"❌ Método {method} NÃO encontrado em ArkmedsClient")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar ArkmedsClient: {e}")
        return False

def main():
    """Executa todos os testes."""
    print("🧪 Testando correções do erro 'list_chamados'...\n")
    
    tests = [
        ("Assinatura de run_incremental_sync", test_run_incremental_sync_signature),
        ("Classe IncrementalSync", test_incremental_sync_class),
        ("Métodos do ArkmedsClient", test_arkmeds_client_methods),
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
        print("🎉 Todas as correções do 'list_chamados' foram aplicadas!")
        return 0
    else:
        print("❌ Ainda há problemas a serem corrigidos.")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
