#!/usr/bin/env python3
"""
Debug das datas no banco de dados.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.db import get_conn
import pandas as pd
from datetime import datetime, date

def check_date_formats():
    """Verificar formatos de data no banco."""
    print("🔍 VERIFICANDO FORMATOS DE DATA...")
    print("="*50)
    
    try:
        with get_conn() as conn:
            # Buscar algumas datas de exemplo
            df = pd.read_sql_query("""
                SELECT 
                    json_extract(payload, '$.data_criacao') as data_criacao,
                    json_extract(payload, '$.data_fechamento') as data_fechamento,
                    created_at as created_at_local
                FROM orders 
                LIMIT 10
            """, conn)
            
        print(f"📊 Total de registros analisados: {len(df)}")
        print("\n📅 DATAS DE CRIAÇÃO:")
        print("-" * 30)
        
        for i, row in df.iterrows():
            print(f"Linha {i+1}:")
            print(f"  data_criacao: {row['data_criacao']} (tipo: {type(row['data_criacao'])})")
            print(f"  data_fechamento: {row['data_fechamento']}")
            print(f"  created_at_local: {row['created_at_local']}")
            
            # Tentar converter data_criacao
            if row['data_criacao']:
                try:
                    # Testa vários formatos
                    formats = [
                        '%Y-%m-%dT%H:%M:%S',
                        '%Y-%m-%d %H:%M:%S', 
                        '%Y-%m-%d',
                        '%d/%m/%Y',
                        '%m/%d/%Y'
                    ]
                    
                    parsed = None
                    for fmt in formats:
                        try:
                            parsed = datetime.strptime(str(row['data_criacao']), fmt)
                            print(f"  ✅ Formato detectado: {fmt} → {parsed}")
                            break
                        except:
                            continue
                    
                    if not parsed:
                        # Tentar pandas
                        try:
                            parsed = pd.to_datetime(row['data_criacao'])
                            print(f"  ✅ Pandas converteu: {parsed}")
                        except:
                            print(f"  ❌ Não foi possível converter")
                            
                except Exception as e:
                    print(f"  ❌ Erro na conversão: {e}")
                    
            print()
        
        print("\n📈 TESTE DE FILTRO DE DATAS:")
        print("-" * 40)
        
        # Testar filtro atual
        today = date.today()
        start_of_month = today.replace(day=1)
        
        print(f"Testando filtro: {start_of_month} até {today}")
        
        df_copy = df.copy()
        df_copy['data_criacao_dt'] = pd.to_datetime(df_copy['data_criacao'], errors='coerce')
        
        print(f"Datas convertidas com pandas:")
        for i, dt in enumerate(df_copy['data_criacao_dt']):
            print(f"  Linha {i+1}: {dt} (válida: {pd.notna(dt)})")
            
        # Aplicar filtro
        start_dt = pd.Timestamp(start_of_month)
        end_dt = pd.Timestamp(today) + pd.Timedelta(days=1)
        
        filtered = df_copy[
            (df_copy['data_criacao_dt'] >= start_dt) &
            (df_copy['data_criacao_dt'] < end_dt)
        ]
        
        print(f"\n📊 Resultado do filtro: {len(filtered)} registros de {len(df_copy)}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    check_date_formats()
