#!/usr/bin/env python3
"""
Script para verificar se falta algum estado e buscar o estado "Aberta"
"""
import asyncio
import json
from app.arkmeds_client.auth import ArkmedsAuth
from app.arkmeds_client.client import ArkmedsClient

async def check_missing_estados():
    """Verifica se há estados adicionais e busca especialmente o ID 1."""
    print("🔍 Verificando estados faltantes...")
    
    auth = ArkmedsAuth.from_secrets()
    client = ArkmedsClient(auth)
    
    try:
        # Buscar algumas OSs para ver se aparece estado ID 1
        print("📋 Buscando OSs para verificar estado ID 1...")
        os_data = await client._get_all_pages("/api/v5/ordem_servico/", {"page_size": 200})
        
        estados_encontrados = {}
        for os in os_data:
            if "estado" in os and os["estado"]:
                estado = os["estado"]
                estado_id = estado.get("id")
                if estado_id and estado_id not in estados_encontrados:
                    estados_encontrados[estado_id] = estado.get("descricao", "")
        
        print(f"🗂️ Estados encontrados em OSs reais ({len(estados_encontrados)}):")
        for estado_id in sorted(estados_encontrados.keys()):
            descricao = estados_encontrados[estado_id]
            print(f"  - ID {estado_id}: {descricao}")
            
        # Verificar se ID 1 existe
        if 1 in estados_encontrados:
            print(f"✅ Estado ID 1 encontrado: {estados_encontrados[1]}")
        else:
            print(f"⚠️ Estado ID 1 não encontrado nas OSs atuais")
            
        return estados_encontrados
        
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(check_missing_estados())
