#!/usr/bin/env python3
"""Script de teste completo para autenticação e uso da API Arkmeds."""

import asyncio
import httpx

async def test_full_flow():
    """Testa o fluxo completo de autenticação e acesso à API."""
    base_url = "https://comg.arkmeds.com"
    email = "rafael.ribeiro@drumondsolucoeshospitalares.com"
    password = "abc123"
    
    async with httpx.AsyncClient(base_url=base_url, timeout=10) as client:
        # Passo 1: Login
        print("1. Fazendo login...")
        try:
            resp = await client.post(
                "/rest-auth/token-auth/",
                json={"email": email, "password": password}
            )
            if resp.status_code == 200:
                data = resp.json()
                token = data.get('token')
                print(f"  ✓ Login bem-sucedido! Token: {token[:50]}...")
            else:
                print(f"  ✗ Erro no login: {resp.status_code} - {resp.text}")
                return
        except Exception as e:
            print(f"  ✗ Erro na requisição de login: {e}")
            return
        
        # Passo 2: Teste com Bearer
        print("\n2. Testando acesso à API com 'Bearer'...")
        headers = {"Authorization": f"Bearer {token}"}
        try:
            resp = await client.get("/api/v3/ordem_servico/", headers=headers, params={"page": 1, "page_size": 1})
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                print("  ✓ Sucesso com Bearer!")
            else:
                print(f"  ✗ Erro: {resp.text}")
        except Exception as e:
            print(f"  ✗ Erro na requisição: {e}")
        
        # Passo 3: Teste com Token
        print("\n3. Testando acesso à API com 'Token'...")
        headers = {"Authorization": f"Token {token}"}
        try:
            resp = await client.get("/api/v3/ordem_servico/", headers=headers, params={"page": 1, "page_size": 1})
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                print("  ✓ Sucesso com Token!")
                data = resp.json()
                print(f"  Total de registros: {data.get('count', 'N/A')}")
            else:
                print(f"  ✗ Erro: {resp.text}")
        except Exception as e:
            print(f"  ✗ Erro na requisição: {e}")
        
        # Passo 4: Teste outros endpoints
        print("\n4. Testando outros endpoints...")
        endpoints = [
            "/api/v3/equipamento/",
            "/api/v3/users/",
        ]
        
        for endpoint in endpoints:
            try:
                resp = await client.get(endpoint, headers={"Authorization": f"Token {token}"}, params={"page": 1, "page_size": 1})
                print(f"  {endpoint}: {resp.status_code}")
                if resp.status_code == 200:
                    data = resp.json()
                    count = data.get('count', 'N/A')
                    print(f"    Total: {count}")
                else:
                    print(f"    Erro: {resp.text}")
            except Exception as e:
                print(f"    Erro: {e}")

if __name__ == "__main__":
    asyncio.run(test_full_flow())
