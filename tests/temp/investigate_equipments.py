#!/usr/bin/env python3
"""
Script para investigar a API de equipamentos /api/v5/company/equipaments/
e /api/v5/equipament/{id} para entender a estrutura real dos dados.
"""

import asyncio
import json
from app.arkmeds_client.auth import ArkmedsAuth
from app.arkmeds_client.client import ArkmedsClient


async def fetch_equipments():
    """Investiga as APIs de equipamentos."""
    print("🔍 Investigando API de equipamentos...")
    
    try:
        # Inicializar cliente
        auth = ArkmedsAuth.from_secrets()
        client = ArkmedsClient(auth)
        
        print("\n📡 1. Buscando equipamentos por empresa (/api/v5/company/equipaments/)...")
        
        # Fazer requisição manual para a API
        http_client = await client._get_client()
        
        # Primeira requisição - lista de equipamentos por empresa
        resp1 = await http_client.get("/api/v5/company/equipaments/", params={"page_size": 10})
        resp1.raise_for_status()
        
        data1 = resp1.json()
        print(f"✅ Status: {resp1.status_code}")
        print(f"📊 Headers relevantes:")
        for header in ['content-type', 'x-total-count']:
            if header in resp1.headers:
                print(f"  {header}: {resp1.headers[header]}")
        
        print(f"\n📋 Estrutura da resposta:")
        print(f"  - Tipo: {type(data1)}")
        if isinstance(data1, dict):
            print(f"  - Chaves: {list(data1.keys())}")
            if 'count' in data1:
                print(f"  - Total de registros: {data1['count']}")
            if 'results' in data1 and data1['results']:
                print(f"  - Primeiros resultados: {len(data1['results'])}")
                
                # Analisar estrutura do primeiro resultado
                first_result = data1['results'][0]
                print(f"\n🏗️ Estrutura do primeiro resultado:")
                print(f"  - Tipo: {type(first_result)}")
                print(f"  - Chaves: {list(first_result.keys()) if isinstance(first_result, dict) else 'não é dict'}")
                
                # Se tem equipamentos aninhados, analisar
                if 'equipamentos' in first_result and first_result['equipamentos']:
                    primeiro_equip = first_result['equipamentos'][0]
                    print(f"\n🔧 Estrutura do primeiro equipamento:")
                    print(f"  - Tipo: {type(primeiro_equip)}")
                    print(f"  - Chaves: {list(primeiro_equip.keys()) if isinstance(primeiro_equip, dict) else 'não é dict'}")
                    
                    # Pegar ID para testar a segunda API
                    equip_id = primeiro_equip.get('id') if isinstance(primeiro_equip, dict) else None
                    
                    if equip_id:
                        print(f"\n📡 2. Buscando detalhes do equipamento {equip_id} (/api/v5/equipament/{equip_id})...")
                        
                        # Segunda requisição - detalhes específicos do equipamento
                        resp2 = await http_client.get(f"/api/v5/equipament/{equip_id}/")
                        resp2.raise_for_status()
                        
                        data2 = resp2.json()
                        print(f"✅ Status: {resp2.status_code}")
                        print(f"📋 Estrutura da resposta de detalhes:")
                        print(f"  - Tipo: {type(data2)}")
                        if isinstance(data2, dict):
                            print(f"  - Chaves: {list(data2.keys())}")
                        
                        # Salvar dados no arquivo para análise
                        result = {
                            "equipments_list": {
                                "status_code": resp1.status_code,
                                "headers": dict(resp1.headers),
                                "data": data1
                            },
                            "equipment_details": {
                                "equipment_id": equip_id,
                                "status_code": resp2.status_code,
                                "headers": dict(resp2.headers),
                                "data": data2
                            }
                        }
                        
                        with open("equipments_api_investigation.json", "w", encoding="utf-8") as f:
                            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
                        
                        print(f"\n💾 Dados salvos em 'equipments_api_investigation.json'")
                        
                        # Análise rápida dos campos importantes
                        print(f"\n🔍 ANÁLISE RÁPIDA:")
                        print(f"📋 Lista de equipamentos:")
                        if 'results' in data1:
                            for company in data1['results'][:3]:  # Mostrar apenas 3 primeiras empresas
                                if 'equipamentos' in company:
                                    print(f"  - Empresa '{company.get('nome', 'sem nome')}': {len(company['equipamentos'])} equipamentos")
                        
                        print(f"\n🔧 Detalhes do equipamento {equip_id}:")
                        if isinstance(data2, dict):
                            for key, value in data2.items():
                                if isinstance(value, (str, int, float, bool)) or value is None:
                                    print(f"  - {key}: {value}")
                                else:
                                    print(f"  - {key}: {type(value).__name__} (complexo)")
                        
                        return result
        
        print("❌ Nenhum equipamento encontrado nos dados")
        return None
        
    except Exception as e:
        print(f"❌ Erro durante a investigação: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(fetch_equipments())
