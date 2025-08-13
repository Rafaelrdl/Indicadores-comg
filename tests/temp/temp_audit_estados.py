#!/usr/bin/env python3
"""
Script temporário para auditar todos os estados de OS na API Arkmeds.
"""
import asyncio
import json
from app.arkmeds_client.auth import ArkmedsAuth
from app.arkmeds_client.client import ArkmedsClient


async def discover_all_estados():
    """Descobre todos os estados possíveis na API."""
    print("🔍 Iniciando descoberta de estados...")

    # Autenticar
    auth = ArkmedsAuth.from_secrets()
    client = ArkmedsClient(auth)

    try:
        # Tentar diferentes endpoints para estados
        endpoints_to_try = [
            "/api/v3/estado_os/",
            "/api/v3/estado_ordem_servico/",
            "/api/v5/estado_ordem_servico/",
            "/api/v3/estados/",
            "/api/v5/estados/",
        ]

        for endpoint in endpoints_to_try:
            print(f"\n📡 Testando endpoint: {endpoint}")
            try:
                # Fazer requisição direta
                resp = await client._request("GET", endpoint)
                data = resp.json()

                print(f"✅ Sucesso! Encontrados dados em {endpoint}")
                print(f"📊 Estrutura da resposta:")
                print(json.dumps(data, indent=2, ensure_ascii=False))

                # Se for paginado, pegar todas as páginas
                if "results" in data:
                    all_estados = await client._get_all_pages(endpoint, {})
                    print(f"\n🗂️ Todos os estados encontrados ({len(all_estados)}):")
                    for estado in all_estados:
                        print(f"  - ID {estado.get('id')}: {estado.get('descricao')}")
                else:
                    print(
                        f"\n🗂️ Estados encontrados ({len(data) if isinstance(data, list) else 1}):"
                    )
                    if isinstance(data, list):
                        for estado in data:
                            print(f"  - ID {estado.get('id')}: {estado.get('descricao')}")

                return data

            except Exception as e:
                print(f"❌ Erro em {endpoint}: {e}")
                continue

        # Se nenhum endpoint funcionou, tentar buscar estados através de OS existentes
        print(f"\n🔄 Nenhum endpoint direto funcionou. Tentando extrair estados de OSs...")

        try:
            # Buscar algumas OSs e ver que estados aparecem
            os_data = await client._get_all_pages("/api/v5/ordem_servico/", {"page_size": 100})

            estados_encontrados = {}
            for os in os_data:
                if "estado" in os and os["estado"]:
                    estado = os["estado"]
                    estado_id = estado.get("id")
                    if estado_id and estado_id not in estados_encontrados:
                        estados_encontrados[estado_id] = estado.get("descricao", "")

            print(f"🗂️ Estados extraídos de OSs ({len(estados_encontrados)}):")
            for estado_id, descricao in sorted(estados_encontrados.items()):
                print(f"  - ID {estado_id}: {descricao}")

            return list(estados_encontrados.items())

        except Exception as e:
            print(f"❌ Erro ao extrair de OSs: {e}")

        print("❌ Não foi possível descobrir estados através da API")
        return None

    finally:
        await client.close()


async def main():
    try:
        result = await discover_all_estados()

        if result:
            print(f"\n✨ Descoberta concluída com sucesso!")
            print(f"💡 Use esses dados para atualizar a classe OSEstado no models.py")
        else:
            print(f"\n⚠️ Não foi possível descobrir todos os estados automaticamente")
            print(f"💡 Considere verificar a documentação da API ou logs do sistema")

    except Exception as e:
        print(f"💥 Erro geral: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
