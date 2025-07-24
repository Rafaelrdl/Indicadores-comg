#!/usr/bin/env python3
"""Script para inspecionar a estrutura dos dados da API."""

import asyncio
import json
import httpx

async def test_api_data_structure():
    """Testa e mostra a estrutura dos dados da API."""
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
        headers = {"Authorization": f"JWT {token}"}
        
        # Buscar primeira OS
        print("\nBuscando dados da API...")
        resp = await client.get(
            "/api/v3/ordem_servico/", 
            headers=headers, 
            params={"page": 1, "page_size": 1}
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"Status: 200 - Sucesso!")
            print(f"Total de registros: {data.get('count', 'N/A')}")
            
            if data.get('results'):
                print("\nPrimeiro item da API:")
                first_item = data['results'][0]
                print(json.dumps(first_item, indent=2, ensure_ascii=False))
                
                # Analisar campos específicos que estão causando problemas
                print("\n--- Análise dos Campos Problemáticos ---")
                print(f"ID: {first_item.get('id')}")
                print(f"tipo_ordem_servico: {first_item.get('tipo_ordem_servico')} (type: {type(first_item.get('tipo_ordem_servico'))})")
                print(f"responsavel: {first_item.get('responsavel')} (type: {type(first_item.get('responsavel'))})")
                print(f"estado: {first_item.get('estado')} (type: {type(first_item.get('estado'))})")
                
        else:
            print(f"Erro: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    asyncio.run(test_api_data_structure())
