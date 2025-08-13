#!/usr/bin/env python3
"""
Script para testar as melhorias na classe User.
"""
import asyncio
from app.arkmeds_client.auth import ArkmedsAuth
from app.arkmeds_client.client import ArkmedsClient
from app.arkmeds_client.models import User


async def test_user_improvements():
    """Testa as melhorias na classe User."""
    print("🔍 Testando melhorias na classe User...")

    # Teste 1: User com apenas ID
    print("\n1. Teste User apenas com ID:")
    user1 = User(id=123, nome="", email="")
    print(f"   Display name: '{user1.display_name}'")
    print(f"   String repr: '{str(user1)}'")

    # Teste 2: User com nome completo
    print("\n2. Teste User com nome:")
    user2 = User(id=456, nome="João Silva", email="joao@test.com")
    print(f"   Display name: '{user2.display_name}'")
    print(f"   String repr: '{str(user2)}'")

    # Teste 3: User com first_name e last_name
    print("\n3. Teste User com first_name/last_name:")
    user3 = User(id=789, nome="", email="", first_name="Maria", last_name="Santos")
    print(f"   Display name: '{user3.display_name}'")
    print(f"   String repr: '{str(user3)}'")

    # Teste 4: User apenas com email
    print("\n4. Teste User apenas com email:")
    user4 = User(id=101, nome="", email="carlos@empresa.com")
    print(f"   Display name: '{user4.display_name}'")
    print(f"   String repr: '{str(user4)}'")

    # Teste 5: Buscar usuários reais da API
    print("\n5. Teste buscar usuários da API:")
    auth = ArkmedsAuth.from_secrets()
    client = ArkmedsClient(auth)

    try:
        users = await client.list_users()
        print(f"   Encontrados {len(users)} usuários:")
        for user in users[:5]:  # Mostrar apenas 5 primeiros
            print(f"   - ID {user.id}: '{user.display_name}' (nome: '{user.nome}')")
    except Exception as e:
        print(f"   ❌ Erro ao buscar usuários: {e}")
    finally:
        await client.close()

    print("\n✅ Testes concluídos!")


if __name__ == "__main__":
    asyncio.run(test_user_improvements())
