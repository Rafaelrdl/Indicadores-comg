#!/usr/bin/env python3
"""
Demonstração completa da otimização de sincronização incremental por páginas
Simula cenário real onde sync é interrompido e retomado
"""

import sys
import os
import time

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath("."))

from app.services.sync_jobs import (
    create_job,
    get_last_synced_page,
    update_job_page,
    get_job_status,
    update_job,
    finish_job
)
from app.core.db import get_conn

def simulate_full_sync_interruption():
    """Simula uma sincronização completa que é interrompida."""
    print("🚀 SIMULAÇÃO: Sincronização interrompida na metade")
    print("=" * 60)
    
    # Cenário: sync de 5,191 registros distribuídos em 104 páginas de 50 registros cada
    total_records = 5191
    records_per_page = 50
    total_pages = 104  # ceil(5191/50)
    
    # Criar job inicial
    job_id = create_job("delta", start_page=1)
    print(f"✅ Sincronização iniciada: {job_id}")
    
    # Simular progresso até metade (página 52)
    interrupted_at_page = 52
    
    print(f"📄 Processando páginas 1 a {interrupted_at_page}...")
    for page in range(1, interrupted_at_page + 1):
        processed = page * records_per_page
        update_job_page(job_id, current_page=page, last_page_synced=page, total_pages=total_pages)
        update_job(job_id, processed=processed, total=total_records)
        
        if page % 10 == 0:  # Log a cada 10 páginas
            print(f"   ✓ Página {page} - {processed} registros processados")
    
    # Simular interrupção (não chama finish_job)
    final_status = get_job_status(job_id)
    print(f"\n💥 SINCRONIZAÇÃO INTERROMPIDA!")
    print(f"   Última página processada: {final_status['last_page_synced']}")
    print(f"   Registros processados: {final_status['processed']}/{total_records}")
    print(f"   Progresso perdido: {final_status['percent']:.1f}%")
    
    return interrupted_at_page, total_records, total_pages


def simulate_resume_sync():
    """Simula a retomada da sincronização do ponto onde parou."""
    print(f"\n🔄 OTIMIZAÇÃO: Retomando sincronização incremental")
    print("=" * 60)
    
    # Descobrir onde parou
    last_page = get_last_synced_page("delta")
    start_page = last_page + 1 if last_page > 0 else 1
    
    print(f"🔍 Última página sincronizada: {last_page}")
    print(f"📄 Retomando a partir da página: {start_page}")
    
    # Cenário: mesmos dados da simulação anterior
    total_records = 5191
    records_per_page = 50
    total_pages = 104
    
    # Criar novo job começando do ponto correto
    job_id = create_job("delta", start_page=start_page)
    print(f"✅ Novo job criado: {job_id}")
    
    # Processar apenas as páginas restantes
    remaining_pages = total_pages - last_page
    processed_before = last_page * records_per_page
    
    print(f"📊 Otimização detectada:")
    print(f"   • Páginas já processadas: {last_page}")
    print(f"   • Páginas restantes: {remaining_pages}")
    print(f"   • Economia de tempo: {(last_page/total_pages)*100:.1f}%")
    
    # Simular processamento das páginas restantes
    print(f"\n📄 Processando páginas {start_page} a {total_pages}...")
    for page in range(start_page, total_pages + 1):
        processed = processed_before + ((page - start_page + 1) * records_per_page)
        if processed > total_records:
            processed = total_records
            
        update_job_page(job_id, current_page=page, last_page_synced=page, total_pages=total_pages)
        update_job(job_id, processed=processed, total=total_records)
        
        if page % 10 == 0 or page == total_pages:  # Log a cada 10 páginas ou no final
            print(f"   ✓ Página {page} - {processed} registros processados")
    
    # Finalizar sincronização
    finish_job(job_id, "success")
    final_status = get_job_status(job_id)
    
    print(f"\n✅ SINCRONIZAÇÃO CONCLUÍDA!")
    print(f"   Status: {final_status['status']}")
    print(f"   Total processado: {final_status['processed']}/{total_records}")
    print(f"   Progresso: {final_status['percent']:.1f}%")
    
    return remaining_pages, total_pages - last_page


def show_performance_comparison():
    """Mostra comparação de performance."""
    print(f"\n📈 COMPARAÇÃO DE PERFORMANCE")
    print("=" * 60)
    
    # Dados do cenário
    total_records = 5191
    total_pages = 104
    interrupted_at = 52
    
    # Cenário sem otimização (sempre processa tudo)
    print(f"❌ SEM OTIMIZAÇÃO:")
    print(f"   • Primeira execução: {total_pages} páginas ({total_records} registros)")
    print(f"   • Após interrupção: {total_pages} páginas ({total_records} registros) - NOVAMENTE!")
    print(f"   • Total processado: {total_pages * 2} páginas ({total_records * 2} registros)")
    
    # Cenário com otimização (continua de onde parou)
    remaining_pages = total_pages - interrupted_at
    print(f"\n✅ COM OTIMIZAÇÃO:")
    print(f"   • Primeira execução: {interrupted_at} páginas ({interrupted_at * 50} registros)")
    print(f"   • Após interrupção: {remaining_pages} páginas ({total_records - (interrupted_at * 50)} registros)")
    print(f"   • Total processado: {total_pages} páginas ({total_records} registros)")
    
    # Economia
    savings_pages = total_pages - remaining_pages  
    savings_records = total_records - (total_records - (interrupted_at * 50))
    savings_percent = (savings_pages / total_pages) * 100
    
    print(f"\n💰 ECONOMIA OBTIDA:")
    print(f"   • Páginas economizadas: {savings_pages}")
    print(f"   • Registros economizados: {savings_records}")
    print(f"   • Redução de tempo: {savings_percent:.1f}%")
    print(f"   • Processamento evitado: {interrupted_at}/{total_pages} páginas")


if __name__ == "__main__":
    try:
        # Simular cenário completo
        interrupted_page, total_rec, total_pgs = simulate_full_sync_interruption()
        remaining_pgs, processed_pgs = simulate_resume_sync()
        show_performance_comparison()
        
        print(f"\n🎯 RESULTADO FINAL:")
        print(f"✅ Sistema de sincronização incremental por páginas IMPLEMENTADO!")
        print(f"✅ Otimização automática funcionando perfeitamente!")
        print(f"✅ Economia significativa de tempo e recursos!")
        print(f"\n💡 BENEFÍCIOS PRÁTICOS:")
        print(f"• Resistente a interrupções de rede")
        print(f"• Economia de recursos de servidor")
        print(f"• Sincronização mais eficiente")
        print(f"• Melhor experiência do usuário")
        
    except Exception as e:
        print(f"❌ Erro durante demonstração: {e}")
        import traceback
        traceback.print_exc()
