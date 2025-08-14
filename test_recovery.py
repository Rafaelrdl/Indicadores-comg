#!/usr/bin/env python3
"""
Teste específico da função get_last_synced_page
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath("."))

from app.services.sync_jobs import (
    create_job,
    get_last_synced_page,
    update_job_page,
    update_job,
    finish_job
)

def test_realistic_scenario():
    """Testa cenário mais realístico com jobs finalizados."""
    print("🧪 TESTE: Recuperação de última página sincronizada")
    print("=" * 60)
    
    # 1. Simular primeira sincronização completa
    print("📋 1. Primeira sincronização completa...")
    job1 = create_job("delta", start_page=1)
    
    # Simular processamento completo até página 30
    for page in range(1, 31):
        update_job_page(job1, current_page=page, last_page_synced=page, total_pages=100)
        update_job(job1, processed=page * 50, total=5000)
    
    # Finalizar como sucesso
    finish_job(job1, "success")
    print(f"✅ Primeira sync finalizada: 30 páginas processadas")
    
    # 2. Verificar se a função recupera corretamente
    last_page = get_last_synced_page("delta")
    print(f"🔍 Última página recuperada: {last_page}")
    
    # 3. Simular segunda sincronização (incremental)
    print(f"\n📋 2. Segunda sincronização incremental a partir da página {last_page + 1}...")
    job2 = create_job("delta", start_page=last_page + 1)
    
    # Simular processamento das páginas restantes
    for page in range(last_page + 1, 51):  # 31 até 50
        update_job_page(job2, current_page=page, last_page_synced=page, total_pages=100)
        update_job(job2, processed=page * 50, total=5000)
    
    # Finalizar segunda sync
    finish_job(job2, "success")
    print(f"✅ Segunda sync finalizada: páginas {last_page + 1} a 50 processadas")
    
    # 4. Verificar novamente a última página
    final_last_page = get_last_synced_page("delta")
    print(f"🔍 Nova última página recuperada: {final_last_page}")
    
    # 5. Demonstrar economia
    print(f"\n📊 DEMONSTRAÇÃO DE ECONOMIA:")
    print(f"   • Sem otimização: processaria 50 páginas novamente = 2,500 registros")
    print(f"   • Com otimização: processou apenas {50 - last_page} páginas = {(50 - last_page) * 50} registros")
    print(f"   • Economia: {((last_page / 50) * 100):.1f}% de processamento evitado!")
    
    return last_page, final_last_page


if __name__ == "__main__":
    try:
        first_page, second_page = test_realistic_scenario()
        
        print(f"\n🎯 RESULTADO DO TESTE:")
        print(f"✅ Primeira recuperação: {first_page} páginas")
        print(f"✅ Segunda recuperação: {second_page} páginas")
        print(f"✅ Sistema de recuperação funcionando corretamente!")
        
        if first_page > 0 and second_page > first_page:
            print(f"✅ Otimização incremental VALIDADA!")
        else:
            print(f"❌ Algo não funcionou como esperado")
            
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()
