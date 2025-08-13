#!/usr/bin/env python3
"""
Script para verificar estrutura de dados dos usuários na API.
"""
import asyncio
import json
from app.arkmeds_client.auth import ArkmedsAuth
from app.arkmeds_client.client import ArkmedsClient


async def check_user_data():
    """Verifica estrutura de dados dos usuários na API."""
    print("🔍 Verificando estrutura de dados dos usuários...")

    auth = ArkmedsAuth.from_secrets()
    client = ArkmedsClient(auth)

    try:
        # Tentar diferentes endpoints para usuários
        endpoints_to_try = [
            "/api/v3/users/",
            "/api/v3/usuario/",
            "/api/v5/users/",
            "/api/v5/usuario/",
        ]

        for endpoint in endpoints_to_try:
            print(f"\n📡 Testando endpoint: {endpoint}")
            try:
                resp = await client._request("GET", endpoint, params={"page_size": 5})
                data = resp.json()

                print(f"✅ Sucesso! Encontrados dados em {endpoint}")
                print(f"📊 Estrutura da resposta:")
                print(json.dumps(data, indent=2, ensure_ascii=False))

                # Se for paginado, mostrar os primeiros resultados
                if "results" in data:
                    users = data["results"]
                    print(f"\n🗂️ Usuários encontrados ({len(users)}):")
                    for user in users:
                        print(f"  - ID {user.get('id')}: {user}")
                        # Verificar campos importantes
                        nome = user.get("nome") or user.get("first_name") or user.get("username")
                        email = user.get("email")
                        print(f"    Nome extraído: '{nome}'")
                        print(f"    Email: '{email}'")
                        print("    ---")

                return data

            except Exception as e:
                print(f"❌ Erro em {endpoint}: {e}")
                continue

        # Se nenhum endpoint funcionou, tentar extrair usuários de OSs
        print(f"\n🔄 Tentando extrair usuários de OSs...")

        try:
            os_data = await client._get_all_pages("/api/v5/ordem_servico/", {"page_size": 50})

            usuarios_encontrados = {}
            for os in os_data:
                responsavel = os.get("responsavel")
                if responsavel:
                    user_id = (
                        responsavel.get("id") if isinstance(responsavel, dict) else responsavel
                    )
                    if user_id and user_id not in usuarios_encontrados:
                        usuarios_encontrados[user_id] = responsavel

            print(f"🗂️ Usuários extraídos de OSs ({len(usuarios_encontrados)}):")
            for user_id, user_data in list(usuarios_encontrados.items())[:10]:
                print(f"  - ID {user_id}: {user_data}")

            return list(usuarios_encontrados.values())

        except Exception as e:
            print(f"❌ Erro ao extrair de OSs: {e}")

        print("❌ Não foi possível descobrir estrutura de usuários através da API")
        return None

    finally:
        await client.close()


async def main():
    try:
        result = await check_user_data()

        if result:
            print(f"\n✨ Descoberta concluída com sucesso!")
            print(f"💡 Use esses dados para melhorar a classe User")
        else:
            print(f"\n⚠️ Não foi possível descobrir estrutura de usuários automaticamente")

    except Exception as e:
        print(f"💥 Erro geral: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
