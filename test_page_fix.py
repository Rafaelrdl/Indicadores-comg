#!/usr/bin/env python3
"""
Teste simplificado para verificar se a correção do loop infinito de páginas funcionou.
"""

import asyncio
import os
import sys

# Adicionar o diretório do app ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import Settings
from app.arkmeds_client.auth import ArkmedsAuth
from app.arkmeds_client.client import ArkmedsClient
from app.services.sync_jobs import get_last_synced_page, clean_running_jobs
from app.services.sync.delta import run_delta_sync_with_progress

async def test_page_fix():
    """Testa se o loop infinito foi corrigido."""
    print("🧪 Testando correção do loop infinito de páginas")
    print("=" * 60)
    
    # Limpar jobs órfãos primeiro
    clean_running_jobs()
    print("✅ Jobs órfãos limpos")
    
    # Verificar última página sincronizada
    last_page = get_last_synced_page("delta")
    next_page = last_page + 1
    print(f"📄 Última página sincronizada: {last_page}")
    print(f"📄 Próxima página a sincronizar: {next_page}")
    
    # Criar cliente da API
    settings = Settings()
    auth = ArkmedsAuth(settings.arkmeds_email, settings.arkmeds_password, settings.arkmeds_base_url)
    client = ArkmedsClient(auth)
    
    try:
        print(f"\n🚀 Iniciando sincronização limitada de 1 página (página {next_page})")
        print("⏱️ TIMEOUT: 60 segundos (cancela se entrar em loop)")
        
        # Executar sincronização com timeout
        result = await asyncio.wait_for(
            run_delta_sync_with_progress(client, ["orders"]),
            timeout=60  # 60 segundos máximo
        )
        
        print(f"\n✅ Sincronização concluída!")
        print(f"📊 Registros sincronizados: {result}")
        
        # Verificar se a página foi atualizada
        new_last_page = get_last_synced_page("delta")
        if new_last_page > last_page:
            print(f"✅ Página atualizada corretamente: {last_page} → {new_last_page}")
            return True
        else:
            print(f"❌ Página não foi atualizada: ainda em {new_last_page}")
            return False
            
    except asyncio.TimeoutError:
        print("\n❌ TIMEOUT: Sincronização cancelada - ainda há loop infinito!")
        return False
    except Exception as e:
        print(f"\n❌ Erro durante sincronização: {e}")
        return False
    finally:
        await client.close()

if __name__ == "__main__":
    result = asyncio.run(test_page_fix())
    if result:
        print("\n🎉 SUCESSO: Correção funcionou!")
        sys.exit(0)
    else:
        print("\n💥 FALHA: Ainda há problemas")
        sys.exit(1)
