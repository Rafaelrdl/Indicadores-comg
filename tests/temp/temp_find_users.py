#!/usr/bin/env python3
"""
Script para descobrir endpoint correto de usuários.
"""
import asyncio
from app.arkmeds_client.auth import ArkmedsAuth
from app.arkmeds_client.client import ArkmedsClient


async def find_users_endpoint():
    """Encontra o endpoint correto para usuários."""
    print("🔍 Buscando endpoint correto para usuários...")

    auth = ArkmedsAuth.from_secrets()
    client = ArkmedsClient(auth)

    try:
        # Descobrir quais endpoints existem testando OSs com expand
        print("📋 Testando OS com dados expandidos...")

        # Tentar buscar OS com expansão de responsável
        try:
            resp = await client._request(
                "GET", "/api/v5/ordem_servico/", params={"page_size": 5, "expand": "responsavel"}
            )
            data = resp.json()

            if "results" in data and data["results"]:
                for os in data["results"]:
                    responsavel = os.get("responsavel")
                    if responsavel and isinstance(responsavel, dict):
                        print(f"✅ Responsável expandido encontrado:")
                        print(f"   {responsavel}")
                        return "expand"

        except Exception as e:
            print(f"❌ Erro com expand: {e}")

        # Tentar endpoint direto de auth/users
        try:
            resp = await client._request("GET", "/api/v3/auth/users/")
            data = resp.json()
            print(f"✅ Encontrado endpoint /api/v3/auth/users/")
            print(f"   Dados: {data}")
            return "/api/v3/auth/users/"
        except Exception as e:
            print(f"❌ Erro em /api/v3/auth/users/: {e}")

        # Tentar técnicos responsáveis
        try:
            resp = await client._request("GET", "/api/v3/responsavel_tecnico/")
            data = resp.json()
            print(f"✅ Encontrado endpoint /api/v3/responsavel_tecnico/")
            print(f"   Dados: {data}")
            return "/api/v3/responsavel_tecnico/"
        except Exception as e:
            print(f"❌ Erro em /api/v3/responsavel_tecnico/: {e}")

        print("❌ Nenhum endpoint de usuários encontrado")
        return None

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(find_users_endpoint())
