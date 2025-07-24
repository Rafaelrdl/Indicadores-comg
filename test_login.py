#!/usr/bin/env python3
"""Script de teste para o endpoint de login da API Arkmeds."""

import asyncio
import httpx

async def test_login():
    """Testa diferentes formatos de login."""
    base_url = "https://comg.arkmeds.com"
    email = "rafael.ribeiro@drumondsolucoeshospitalares.com"
    password = "abc123"
    
    endpoints = [
        "/rest-auth/token-auth/",
        "/rest-auth/login/",
        "/api/v5/auth/login/",
        "/api/v3/auth/login",
    ]
    
    async with httpx.AsyncClient(base_url=base_url, timeout=10) as client:
        for endpoint in endpoints:
            print(f"\nTestando endpoint: {endpoint}")
            
            # Teste 1: username/password
            try:
                resp = await client.post(
                    endpoint,
                    json={"username": email, "password": password}
                )
                print(f"  Teste 1 (username/password): {resp.status_code}")
                if resp.status_code == 200:
                    print(f"  Sucesso! Resposta: {resp.json()}")
                    return
                elif resp.status_code == 400:
                    print(f"  Bad Request: {resp.text}")
                else:
                    print(f"  Erro: {resp.text}")
            except Exception as e:
                print(f"  Erro na requisição: {e}")
            
            # Teste 2: email/password
            try:
                resp = await client.post(
                    endpoint,
                    json={"email": email, "password": password}
                )
                print(f"  Teste 2 (email/password): {resp.status_code}")
                if resp.status_code == 200:
                    print(f"  Sucesso! Resposta: {resp.json()}")
                    return
                elif resp.status_code == 400:
                    print(f"  Bad Request: {resp.text}")
                else:
                    print(f"  Erro: {resp.text}")
            except Exception as e:
                print(f"  Erro na requisição: {e}")

if __name__ == "__main__":
    asyncio.run(test_login())
