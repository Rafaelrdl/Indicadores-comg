#!/usr/bin/env python3
"""
Script para descobrir todos os tipos de OS na API Arkmeds.
"""
import asyncio
import json
from app.arkmeds_client.auth import ArkmedsAuth
from app.arkmeds_client.client import ArkmedsClient

async def discover_tipos_os():
    """Descobre todos os tipos de OS possíveis na API."""
    print("🔍 Iniciando descoberta de tipos de OS...")
    
    auth = ArkmedsAuth.from_secrets()
    client = ArkmedsClient(auth)
    
    try:
        # Tentar diferentes endpoints para tipos
        endpoints_to_try = [
            "/api/v3/tipo_servico/",
            "/api/v3/tipo_ordem_servico/", 
            "/api/v5/tipo_ordem_servico/",
            "/api/v3/tipos/",
        ]
        
        for endpoint in endpoints_to_try:
            print(f"\n📡 Testando endpoint: {endpoint}")
            try:
                resp = await client._request("GET", endpoint)
                data = resp.json()
                
                print(f"✅ Sucesso! Encontrados dados em {endpoint}")
                print(f"📊 Estrutura da resposta:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                # Se for paginado, pegar todas as páginas
                if "results" in data:
                    all_tipos = await client._get_all_pages(endpoint, {})
                    print(f"\n🗂️ Todos os tipos encontrados ({len(all_tipos)}):")
                    for tipo in sorted(all_tipos, key=lambda x: x.get('id', 0)):
                        print(f"  - ID {tipo.get('id')}: {tipo.get('descricao')}")
                else:
                    print(f"\n🗂️ Tipos encontrados ({len(data) if isinstance(data, list) else 1}):")
                    if isinstance(data, list):
                        for tipo in sorted(data, key=lambda x: x.get('id', 0)):
                            print(f"  - ID {tipo.get('id')}: {tipo.get('descricao')}")
                
                return data
                
            except Exception as e:
                print(f"❌ Erro em {endpoint}: {e}")
                continue
        
        # Se nenhum endpoint funcionou, tentar extrair tipos através de OSs existentes
        print(f"\n🔄 Nenhum endpoint direto funcionou. Tentando extrair tipos de OSs...")
        
        try:
            os_data = await client._get_all_pages("/api/v5/ordem_servico/", {"page_size": 200})
            
            tipos_encontrados = {}
            for os in os_data:
                if "tipo_servico" in os and os["tipo_servico"]:
                    tipo_id = os["tipo_servico"]
                    if tipo_id and tipo_id not in tipos_encontrados:
                        tipos_encontrados[tipo_id] = f"Tipo {tipo_id}"  # Placeholder
            
            print(f"🗂️ IDs de tipos extraídos de OSs ({len(tipos_encontrados)}):")
            for tipo_id in sorted(tipos_encontrados.keys()):
                print(f"  - ID {tipo_id}")
                
            return list(tipos_encontrados.keys())
            
        except Exception as e:
            print(f"❌ Erro ao extrair de OSs: {e}")
        
        print("❌ Não foi possível descobrir tipos através da API")
        return None
        
    finally:
        await client.close()

async def main():
    try:
        result = await discover_tipos_os()
        
        if result:
            print(f"\n✨ Descoberta concluída com sucesso!")
            print(f"💡 Use esses dados para criar o enum TipoOS")
        else:
            print(f"\n⚠️ Não foi possível descobrir todos os tipos automaticamente")
            
    except Exception as e:
        print(f"💥 Erro geral: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
