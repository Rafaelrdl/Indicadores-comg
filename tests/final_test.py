#!/usr/bin/env python3
"""
Teste final de validação das correções implementadas.

Este script testa:
1. Conexão e leitura do banco SQLite
2. Funcionamento dos controles de refresh
3. Sistema de logging
4. Migração do banco de dados
"""
import sys
import os

# Adicionar app ao path
sys.path.append(os.path.join(os.path.dirname(__file__)))

def test_sqlite_integration():
    """Testa integração com SQLite."""
    print("🧪 Testando integração SQLite...")
    
    try:
        from app.services.repository import get_orders_df, get_database_stats
        from app.core.logging import app_logger
        
        # Testar stats do banco
        stats = get_database_stats()
        print(f"   ✅ Stats obtidas: {stats['orders_count']} ordens, {stats['database_size_mb']:.2f} MB")
        
        # Testar leitura de ordens
        df = get_orders_df()
        print(f"   ✅ DataFrame carregado: {len(df)} registros")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro na integração SQLite: {e}")
        return False

def test_refresh_controls():
    """Testa componentes de refresh."""
    print("🧪 Testando componentes de refresh...")
    
    try:
        from app.ui.components.refresh_controls import render_refresh_controls
        from app.ui.components.status_alerts import check_global_status
        
        # Testar verificação de status
        status = check_global_status(['orders', 'equipments'])
        print(f"   ✅ Status verificado: {status['total_records']} total records")
        
        print("   ✅ Componentes de refresh importados com sucesso")
        return True
        
    except Exception as e:
        print(f"   ❌ Erro nos componentes de refresh: {e}")
        return False

def test_logging_system():
    """Testa sistema de logging."""
    print("🧪 Testando sistema de logging...")
    
    try:
        from app.core.logging import app_logger
        
        # Testar métodos de logging
        app_logger.log_info("Teste de info")
        app_logger.log_warning("Teste de warning")
        app_logger.log_error("Teste de error")
        
        print("   ✅ Sistema de logging funcionando")
        return True
        
    except Exception as e:
        print(f"   ❌ Erro no sistema de logging: {e}")
        return False

def test_database_migration():
    """Testa migração do banco de dados."""
    print("🧪 Testando migração do banco...")
    
    try:
        from app.core.db import get_conn
        
        # Verificar se a coluna synced_at existe
        conn = get_conn()
        cursor = conn.execute("PRAGMA table_info(sync_state)")
        columns = [info[1] for info in cursor.fetchall()]
        
        required_columns = ['synced_at', 'last_id', 'sync_type']
        missing = [col for col in required_columns if col not in columns]
        
        if missing:
            print(f"   ❌ Colunas faltantes: {missing}")
            return False
        else:
            print("   ✅ Todas as colunas necessárias estão presentes")
            return True
            
    except Exception as e:
        print(f"   ❌ Erro na verificação do banco: {e}")
        return False

def main():
    """Executa todos os testes."""
    print("🚀 Iniciando validação final das correções...")
    print("=" * 50)
    
    tests = [
        test_database_migration,
        test_sqlite_integration, 
        test_logging_system,
        test_refresh_controls,
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
        print("🎉 Todas as correções foram aplicadas com sucesso!")
        print("✅ Sistema pronto para uso")
        return True
    else:
        print("⚠️ Alguns testes falharam")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
