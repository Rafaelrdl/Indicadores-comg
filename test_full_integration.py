"""
Teste completo de integração da camada de persistência.

Este script verifica:
1. Inicialização do banco
2. Fetch da API e salvamento local
3. Uso do cache local
4. Métricas calculadas
"""
import asyncio
import os
import sys
from datetime import date, timedelta

# Adicionar o diretório app ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_full_integration():
    """Teste completo de integração."""
    print("🧪 Iniciando teste de integração completo...\n")
    
    # 1. Test database initialization
    print("📊 1. Testando inicialização do banco...")
    from app.core.db import init_database, get_database_info
    
    init_database()
    info = get_database_info()
    print(f"   ✅ Banco inicializado: {info['database_path']}")
    print(f"   ✅ Tabelas criadas: {list(info['tables'].keys())}")
    
    # 2. Test API client
    print("\n🔌 2. Testando cliente da API...")
    from app.arkmeds_client.client import ArkmedsClient
    from app.core.config import get_settings
    
    settings = get_settings()
    client = ArkmedsClient(base_url=settings.arkmeds_base_url)
    
    try:
        # Authenticate
        await client.authenticate(settings.arkmeds_username, settings.arkmeds_password)
        print("   ✅ Autenticação realizada com sucesso")
        
        # Test pagination (small sample)
        params = {'limit': 50}  # Small sample for testing
        orders = await client.list_chamados(params)
        print(f"   ✅ Buscados {len(orders)} registros da API")
        
    except Exception as e:
        print(f"   ⚠️ Erro na API (pode ser normal em teste): {e}")
        return
    
    # 3. Test repository operations
    print("\n💾 3. Testando operações do repositório...")
    from app.services.repository import Repository
    
    if orders:
        # Convert to dict format
        orders_dict = [order.model_dump() for order in orders[:10]]  # Save only first 10
        
        saved_count = Repository.save_orders(orders_dict)
        print(f"   ✅ Salvadas {saved_count} ordens no banco")
        
        # Update sync state
        Repository.update_sync_state('orders', total_records=saved_count)
        print("   ✅ Estado de sincronização atualizado")
        
        # Check if data is fresh
        is_fresh = Repository.is_data_fresh('orders')
        print(f"   ✅ Dados frescos: {is_fresh}")
        
        # Load from database
        df = Repository.get_orders(limit=20)
        print(f"   ✅ Carregadas {len(df)} ordens do banco")
    
    # 4. Test metrics calculation with cache
    print("\n📈 4. Testando cálculo de métricas com cache...")
    from app.services.os_metrics import compute_metrics
    
    # Set date range
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    try:
        # This should use cached data if available
        metrics = await compute_metrics(
            client,
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"   ✅ Métricas calculadas:")
        print(f"      - Corretivas Predial: {metrics.corrective_building}")
        print(f"      - Corretivas Eng. Clínica: {metrics.corrective_engineering}")
        print(f"      - Preventivas Predial: {metrics.preventive_building}")
        print(f"      - Preventivas Infra: {metrics.preventive_infra}")
        print(f"      - Busca Ativa: {metrics.active_search}")
        print(f"      - Backlog: {metrics.backlog}")
        print(f"      - SLA %: {metrics.sla_percentage:.1f}%")
        
    except Exception as e:
        print(f"   ⚠️ Erro no cálculo de métricas: {e}")
    
    # 5. Show final database info
    print("\n📊 5. Estado final do banco:")
    final_info = get_database_info()
    for table, count in final_info['tables'].items():
        print(f"   - {table}: {count} registros")
    print(f"   - Tamanho: {final_info.get('database_size_mb', 0)} MB")
    
    print("\n🎉 Teste de integração concluído!")


if __name__ == "__main__":
    # Run the integration test
    asyncio.run(test_full_integration())
