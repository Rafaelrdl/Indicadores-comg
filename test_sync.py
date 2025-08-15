#!/usr/bin/env python3
"""
Testar a sincronização manual para verificar se está funcionando
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.abspath("."))

from app.arkmeds_client.auth import ArkmedsAuth
from app.arkmeds_client.client import ArkmedsClient
from app.core.config import get_settings
from app.services.sync.delta import run_delta_sync_with_progress
from app.services.sync_jobs import get_running_job

async def test_manual_sync():
    """Testa sincronização manual"""
    print("🧪 TESTANDO SINCRONIZAÇÃO MANUAL")
    print("=" * 50)
    
    # Verificar se há job rodando
    running = get_running_job()
    if running:
        print(f"⚠️ Há um job em execução: {running['job_id']}")
        print("   Aguarde a conclusão ou limpe jobs órfãos primeiro")
        return
    
    print("✅ Nenhum job em execução - pode iniciar nova sincronização")
    
    # Obter configurações
    settings = get_settings()
    
    if not settings.arkmeds_email or not settings.arkmeds_password:
        print("❌ Credenciais não configuradas")
        print("   Configure ARKMEDS_EMAIL e ARKMEDS_PASSWORD no .env")
        return
    
    print(f"📧 Email configurado: {settings.arkmeds_email}")
    print(f"🌐 Base URL: {settings.arkmeds_base_url}")
    
    try:
        print("\n🔐 Criando cliente da API...")
        auth = ArkmedsAuth(
            email=settings.arkmeds_email,
            password=settings.arkmeds_password,
            base_url=settings.arkmeds_base_url,
            token=settings.arkmeds_token,
        )
        
        client = ArkmedsClient(auth)
        
        print("🚀 Iniciando sincronização incremental...")
        result = await run_delta_sync_with_progress(client, ["orders"])
        
        print(f"\n✅ Sincronização concluída!")
        print(f"   Registros processados: {result}")
        
        # Verificar status final
        final_job = get_running_job()
        if final_job:
            print(f"📊 Job ainda rodando: {final_job['job_id']}")
        else:
            print("🎉 Nenhum job em execução - sincronização finalizada")
            
    except Exception as e:
        print(f"❌ Erro durante sincronização: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_manual_sync())
