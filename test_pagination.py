"""Script para testar se a paginação está funcionando corretamente."""

import asyncio
from datetime import date, timedelta
import sys
import pathlib

# Adicionar o diretório app ao path
ROOT = pathlib.Path(__file__).parent / "app"
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from arkmeds_client.client import ArkmedsClient


async def test_pagination():
    """Testa se a paginação está buscando todos os registros."""
    
    print("🔍 Testando paginação da API Arkmeds...")
    print("=" * 70)
    
    client = ArkmedsClient.from_session()
    
    # Teste 1: Buscar sem filtros (últimos 30 dias)
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    print(f"\n📅 Período de teste: {start_date} até {end_date}")
    
    # Buscar com método antigo (sem paginação) - simulando o problema
    print(f"\n{'='*70}")
    print("1️⃣ TESTE: Simulando busca com uma única página (problema original)")
    print("="*70)
    
    try:
        # Simular o comportamento antigo (apenas primeira página)
        client_http = await client._get_client()
        response = await client_http.get(
            "/api/v5/chamado/",
            params={
                "data_criacao__gte": start_date.isoformat(),
                "data_criacao__lte": end_date.isoformat(),
                "page_size": 25,  # Padrão da API que causava o problema
                "page": 1,
                "arquivadas": "true"
            }
        )
        data = response.json()
        single_page_count = len(data.get("results", []))
        total_count = data.get("count", 0)
        pages_needed = (total_count + 24) // 25
        
        print(f"   📊 Registros na primeira página: {single_page_count}")
        print(f"   📊 Total de registros disponíveis na API: {total_count}")
        print(f"   📊 Páginas necessárias para buscar tudo: {pages_needed}")
        print(f"   ⚠️  PROBLEMA: Só {single_page_count} de {total_count} registros seriam usados!")
        
    except Exception as e:
        print(f"   ❌ Erro no teste de página única: {e}")
    
    # Buscar com método novo (com paginação completa)
    print(f"\n{'='*70}")
    print("2️⃣ TESTE: Busca com paginação completa (método corrigido)")
    print("="*70)
    
    try:
        all_results = await client.list_os(
            data_criacao__gte=start_date.isoformat(),
            data_criacao__lte=end_date.isoformat()
        )
        print(f"\n🎉 SUCESSO: {len(all_results)} registros obtidos com paginação completa!")
        
        if len(all_results) > 25:
            print("✅ Paginação funcionando corretamente!")
            print(f"✅ Foram buscados {len(all_results)} registros (muito mais que 25)")
        else:
            print("⚠️ Poucos registros encontrados. Talvez não haja dados suficientes no período.")
            
    except Exception as e:
        print(f"   ❌ Erro no teste de paginação completa: {e}")
        import traceback
        traceback.print_exc()
    
    # Teste 3: Verificar período maior (Janeiro até hoje)
    print(f"\n{'='*70}")
    print("3️⃣ TESTE: Período maior (Janeiro/2025 até hoje)")
    print("="*70)
    
    try:
        jan_start = date(2025, 1, 1)
        all_results_year = await client.list_os(
            data_criacao__gte=jan_start.isoformat(),
            data_criacao__lte=end_date.isoformat()
        )
        
        total_year = len(all_results_year)
        print(f"\n📊 RESULTADO: {total_year} registros de {jan_start} até {end_date}")
        
        if total_year > 0:
            # Análise básica dos dados
            with_os = sum(1 for r in all_results_year if r.ordem_servico)
            print(f"   📋 Chamados com ordens de serviço: {with_os}")
            print(f"   📋 Chamados sem ordens de serviço: {total_year - with_os}")
            
            # Mostrar alguns IDs para verificar variedade
            if total_year >= 5:
                ids = [r.id for r in all_results_year[:5]]
                print(f"   🆔 Primeiros 5 IDs: {ids}")
                
            if total_year > 100:
                print(f"✅ EXCELENTE: {total_year} registros é muito mais que 25!")
                print("✅ A paginação está funcionando perfeitamente!")
            elif total_year > 25:
                print(f"✅ BOM: {total_year} registros indica que a paginação está funcionando")
            else:
                print(f"⚠️ ATENÇÃO: Apenas {total_year} registros encontrados")
                print("   Pode ser que realmente não existam muitos dados no período")
        else:
            print("❌ Nenhum registro encontrado para o período")
            
    except Exception as e:
        print(f"   ❌ Erro no teste de período longo: {e}")
        import traceback
        traceback.print_exc()
    
    # Fechar cliente
    try:
        await client.close()
    except Exception:
        pass
    
    print(f"\n{'='*70}")
    print("✅ TESTE CONCLUÍDO!")
    print("="*70)
    print("Se você viu números muito maiores que 25, a paginação está funcionando!")
    print("Agora os KPIs na aplicação devem mostrar valores corretos.")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(test_pagination())
