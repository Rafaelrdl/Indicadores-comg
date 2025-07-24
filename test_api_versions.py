#!/usr/bin/env python3
"""Script de teste para diferentes versões da API Arkmeds."""

import asyncio
import httpx

async def test_api_versions():
    """Testa diferentes versões da API."""
    base_url = "https://comg.arkmeds.com"
    email = "rafael.ribeiro@drumondsolucoeshospitalares.com"
    password = "abc123"
    
    async with httpx.AsyncClient(base_url=base_url, timeout=10) as client:
        # Login
        print("Fazendo login...")
        resp = await client.post(
            "/rest-auth/token-auth/",
            json={"email": email, "password": password}
        )
        token = resp.json().get('token')
        headers = {"Authorization": f"Token {token}"}
        
        # Testar diferentes endpoints
        endpoints = [
            # API v3
            "/api/v3/ordem_servico/",
            "/api/v3/equipamento/",
            "/api/v3/users/",
            
            # API v5 (baseado na documentação)
            "/api/v5/ordem_servico/",
            "/api/v5/equipamento/",
            "/api/v5/company/",
            "/api/v5/chamado/",
            "/api/v5/oficina/",
            
            # API v2
            "/api/v2/part/",
            "/api/v2/part_type/",
            "/api/v2/part_item/",
        ]
        
        for endpoint in endpoints:
            try:
                resp = await client.get(endpoint, headers=headers, params={"page": 1, "page_size": 1})
                status = resp.status_code
                
                if status == 200:
                    try:
                        data = resp.json()
                        count = data.get('count', 'N/A')
                        print(f"✓ {endpoint}: {status} (count: {count})")
                    except:
                        print(f"✓ {endpoint}: {status} (response não é JSON)")
                elif status == 404:
                    print(f"✗ {endpoint}: {status} (não encontrado)")
                elif status == 403:
                    print(f"✗ {endpoint}: {status} (sem permissão)")
                else:
                    print(f"? {endpoint}: {status}")
                    
            except Exception as e:
                print(f"✗ {endpoint}: erro - {e}")

if __name__ == "__main__":
    asyncio.run(test_api_versions())
