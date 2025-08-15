#!/usr/bin/env python3
"""
Teste das correções de filtro de data.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.db import get_conn
import pandas as pd
from datetime import date

def test_date_filtering():
    """Testar filtros de data corrigidos."""
    print("🧪 TESTANDO FILTROS DE DATA CORRIGIDOS...")
    print("="*60)
    
    # Query corrigida
    sql = """
        SELECT
            json_extract(payload, '$.id') as id,
            json_extract(payload, '$.chamados') as chamados,
            json_extract(payload, '$.ordem_servico.data_criacao') as data_criacao,
            json_extract(payload, '$.ordem_servico.estado') as estado,
            json_extract(payload, '$.ordem_servico.numero') as numero,
            created_at
        FROM orders
        WHERE json_extract(payload, '$.id') IS NOT NULL
        ORDER BY json_extract(payload, '$.ordem_servico.data_criacao') DESC
        LIMIT 10
    """
    
    try:
        with get_conn() as conn:
            df = pd.read_sql_query(sql, conn)
            
        print(f"📊 Registros carregados: {len(df)}")
        print("\n📅 DATAS ENCONTRADAS:")
        print("-" * 40)
        
        for i, row in df.iterrows():
            print(f"ID {row['id']}: {row['data_criacao']}")
        
        # Testar conversão de data
        print(f"\n🔄 TESTANDO CONVERSÃO DE DATAS:")
        print("-" * 40)
        
        def parse_brazilian_date(date_str):
            """Converte data do formato '19/04/23 - 15:58' para datetime."""
            if pd.isna(date_str) or date_str is None:
                return None
            try:
                # Formato: "19/04/23 - 15:58"
                date_part = str(date_str).split(' - ')[0]  # "19/04/23"
                return pd.to_datetime(date_part, format='%d/%m/%y')
            except:
                try:
                    # Tentar outros formatos possíveis
                    return pd.to_datetime(date_str, errors='coerce')
                except:
                    return None
        
        df['data_criacao_dt'] = df['data_criacao'].apply(parse_brazilian_date)
        
        for i, row in df.iterrows():
            original = row['data_criacao']
            converted = row['data_criacao_dt']
            status = "✅" if pd.notna(converted) else "❌"
            print(f"{status} {original} → {converted}")
        
        # Testar filtro
        print(f"\n📈 TESTANDO FILTRO DE PERÍODO:")
        print("-" * 40)
        
        # Filtro para 2023
        start_date = date(2023, 1, 1)
        end_date = date(2023, 12, 31)
        
        start_dt = pd.Timestamp(start_date)
        end_dt = pd.Timestamp(end_date) + pd.Timedelta(days=1)
        
        filtered = df[
            df['data_criacao_dt'].notna() &
            (df['data_criacao_dt'] >= start_dt) &
            (df['data_criacao_dt'] < end_dt)
        ]
        
        print(f"Período: {start_date} a {end_date}")
        print(f"Registros filtrados: {len(filtered)} de {len(df)}")
        
        if len(filtered) > 0:
            print("\n📋 REGISTROS NO PERÍODO:")
            for i, row in filtered.iterrows():
                print(f"  ID {row['id']}: {row['data_criacao']} → {row['data_criacao_dt'].strftime('%d/%m/%Y')}")
        
        # Filtro mais amplo se necessário
        if len(filtered) == 0:
            print("\n🔍 Testando período mais amplo (2020-2025)...")
            start_date_wide = date(2020, 1, 1)
            end_date_wide = date(2025, 12, 31)
            
            start_dt_wide = pd.Timestamp(start_date_wide)
            end_dt_wide = pd.Timestamp(end_date_wide) + pd.Timedelta(days=1)
            
            filtered_wide = df[
                df['data_criacao_dt'].notna() &
                (df['data_criacao_dt'] >= start_dt_wide) &
                (df['data_criacao_dt'] < end_dt_wide)
            ]
            
            print(f"Registros no período amplo: {len(filtered_wide)} de {len(df)}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_date_filtering()
