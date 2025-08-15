#!/usr/bin/env python3
"""
Script para testar os dados no banco SQLite e ver como estão estruturados.
"""

import os
import sys

# Adicionar o diretório do app ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.repository import get_database_stats, get_orders_df, query_df
import pandas as pd

def test_database():
    """Testa os dados no banco SQLite"""
    print("🔍 ANÁLISE DO BANCO SQLITE")
    print("=" * 50)
    
    # Estatísticas gerais
    stats = get_database_stats()
    print(f"📊 Ordens: {stats.get('orders_count', 0)}")
    print(f"📊 Equipamentos: {stats.get('equipments_count', 0)}")  
    print(f"📊 Técnicos: {stats.get('technicians_count', 0)}")
    print(f"💾 Tamanho do banco: {stats.get('database_size_mb', 0)} MB")
    
    # Últimas sincronizações
    last_syncs = stats.get('last_syncs', [])
    if last_syncs:
        print("\n📅 Últimas sincronizações:")
        for sync in last_syncs:
            resource = sync.get('resource', 'N/A')
            synced_at = sync.get('synced_at', sync.get('updated_at', 'N/A'))
            total = sync.get('total_records', 'N/A')
            print(f"   {resource}: {synced_at} ({total} registros)")
    
    # Amostra das ordens
    print("\n📋 AMOSTRA DAS ORDENS:")
    print("-" * 30)
    
    # Buscar algumas ordens
    df = get_orders_df(limit=3)
    if not df.empty:
        print(f"✅ {len(df)} ordens encontradas")
        print("Colunas disponíveis:")
        for col in df.columns:
            print(f"  - {col}")
        
        # Mostrar primeiros registros
        print("\nPrimeiros registros:")
        print(df.head())
        
        # Verificar dados específicos importantes
        if 'estado' in df.columns:
            estados_unicos = df['estado'].unique()
            print(f"\n🏷️ Estados únicos: {list(estados_unicos)}")
            
        if 'tipo_servico' in df.columns:
            tipos_unicos = df['tipo_servico'].unique()
            print(f"🔧 Tipos de serviço únicos: {list(tipos_unicos)[:5]}")  # Apenas primeiros 5
            
        # Status das ordens (abertas/fechadas)
        if 'data_fechamento' in df.columns:
            abertas = df['data_fechamento'].isna().sum()
            fechadas = df['data_fechamento'].notna().sum()
            print(f"📊 Status: {abertas} abertas, {fechadas} fechadas")
            
    else:
        print("❌ Nenhuma ordem encontrada")
        
    # Buscar dados brutos para debug
    print("\n🔍 DADOS BRUTOS (SQL direto):")
    print("-" * 35)
    
    raw_sql = """
        SELECT 
            json_extract(payload, '$.id') as id,
            json_extract(payload, '$.data_criacao') as data_criacao,
            json_extract(payload, '$.data_fechamento') as data_fechamento,
            json_extract(payload, '$.ordem_servico.estado') as estado,
            json_extract(payload, '$.ordem_servico.tipo_servico.nome') as tipo_nome
        FROM orders 
        LIMIT 5
    """
    
    raw_df = query_df(raw_sql)
    if not raw_df.empty:
        print("✅ Dados brutos encontrados:")
        print(raw_df.to_string())
    else:
        print("❌ Nenhum dado bruto encontrado")

if __name__ == "__main__":
    test_database()
