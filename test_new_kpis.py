#!/usr/bin/env python3
"""
Script para testar os KPIs calculados com a nova implementação.
"""

import os
import sys

# Adicionar o diretório do app ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Importar as funções da nova implementação
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'pages'))

# Simular imports sem streamlit context
import pandas as pd
from app.core.db import get_conn

def test_new_kpi_calculation():
    """Testa os KPIs com a nova query SQL."""
    print("🧪 TESTANDO NOVA IMPLEMENTAÇÃO DE KPIs")
    print("=" * 50)
    
    # Query SQL corrigida da nova implementação
    sql = """
        SELECT
            json_extract(payload, '$.id') as id,
            json_extract(payload, '$.chamados') as chamados,
            json_extract(payload, '$.data_criacao') as data_criacao,
            json_extract(payload, '$.data_fechamento') as data_fechamento,
            json_extract(payload, '$.ordem_servico.estado') as estado,
            json_extract(payload, '$.ordem_servico.numero') as numero,
            json_extract(payload, '$.ordem_servico.tipo_servico.id') as tipo_id,
            json_extract(payload, '$.ordem_servico.tipo_servico.nome') as tipo_nome,
            json_extract(payload, '$.responsavel_id') as responsavel_id,
            CASE 
                WHEN json_extract(payload, '$.data_fechamento') IS NOT NULL 
                THEN 'FECHADA' 
                ELSE 'ABERTA' 
            END as status
        FROM orders
        WHERE json_extract(payload, '$.id') IS NOT NULL
        ORDER BY json_extract(payload, '$.data_criacao') DESC
        LIMIT 100
    """
    
    try:
        with get_conn() as conn:
            df = pd.read_sql_query(sql, conn)
            
        print(f"✅ Query executada com sucesso!")
        print(f"📊 Registros carregados: {len(df)}")
        
        if df.empty:
            print("❌ Nenhum dado encontrado")
            return
            
        # Mostrar amostra dos dados
        print("\n📋 AMOSTRA DOS DADOS (primeiras 5 linhas):")
        print("-" * 60)
        print(df[['id', 'chamados', 'data_criacao', 'estado', 'numero', 'status']].head())
        
        # Calcular KPIs básicos
        print(f"\n📈 KPIs CALCULADOS:")
        print("-" * 25)
        
        total_orders = len(df)
        closed_orders = len(df[df['status'] == 'FECHADA'])
        open_orders = len(df[df['status'] == 'ABERTA'])
        
        print(f"📊 Total de ordens: {total_orders}")
        print(f"✅ Fechadas: {closed_orders}")
        print(f"🔄 Abertas: {open_orders}")
        
        # KPIs por estado
        if 'estado' in df.columns:
            estado_counts = df['estado'].value_counts().fillna(0)
            print(f"\n🏷️ DISTRIBUIÇÃO POR ESTADO:")
            for estado, count in estado_counts.items():
                print(f"   Estado {estado}: {count} ordens")
        
        # SLA básico
        sla_percentage = (closed_orders / total_orders * 100) if total_orders > 0 else 0.0
        print(f"\n📈 SLA: {sla_percentage:.1f}%")
        
        # Verificar dados não nulos
        print(f"\n🔍 QUALIDADE DOS DADOS:")
        print(f"   IDs válidos: {df['id'].notna().sum()}/{len(df)}")
        print(f"   Estados válidos: {df['estado'].notna().sum()}/{len(df)}")
        print(f"   Números válidos: {df['numero'].notna().sum()}/{len(df)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na query: {e}")
        return False

if __name__ == "__main__":
    test_new_kpi_calculation()
