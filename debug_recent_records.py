#!/usr/bin/env python3
"""
Debug das datas - verificando registros mais recentes por garantia.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.db import get_conn
import pandas as pd
import json
from datetime import datetime, date

def check_recent_records():
    """Verificar registros mais recentes que devem ter data_criacao."""
    print("🔍 VERIFICANDO REGISTROS MAIS RECENTES...")
    print("="*60)
    
    try:
        with get_conn() as conn:
            # Primeiro, vamos verificar as colunas disponíveis
            columns_df = pd.read_sql_query("PRAGMA table_info(orders)", conn)
            print("📋 Colunas disponíveis na tabela orders:")
            for _, col in columns_df.iterrows():
                print(f"  - {col['name']} ({col['type']})")
            
            # Buscar os registros mais recentes pelo created_at (timestamp local)
            df = pd.read_sql_query("""
                SELECT 
                    id,
                    payload,
                    created_at
                FROM orders 
                ORDER BY created_at DESC
                LIMIT 5
            """, conn)
            
        print(f"📊 Total de registros analisados: {len(df)}")
        print("\n🧪 ANÁLISE DA ESTRUTURA JSON:")
        print("-" * 50)
        
        for i, row in df.iterrows():
            print(f"\n📋 REGISTRO {i+1}:")
            print(f"  ID: {row['id']}")
            print(f"  created_at: {row['created_at']}")
            
            if row['payload']:
                try:
                    # Parse do JSON
                    payload = json.loads(row['payload'])
                    print(f"  ✅ JSON válido")
                    
                    # Verificar estrutura
                    print(f"  📋 Campos principais:")
                    for key in ['id', 'data_criacao', 'data_fechamento', 'chamados']:
                        if key in payload:
                            print(f"    - {key}: {payload[key]} (tipo: {type(payload[key])})")
                        else:
                            print(f"    - {key}: ❌ AUSENTE")
                    
                    # Verificar ordem_servico se existe
                    if 'ordem_servico' in payload:
                        print(f"  🔧 ordem_servico:")
                        os_data = payload['ordem_servico']
                        for key in ['estado', 'numero', 'tipo_servico']:
                            if key in os_data:
                                print(f"    - {key}: {os_data[key]}")
                            else:
                                print(f"    - {key}: ❌ AUSENTE")
                    
                    # Testar extração SQL equivalente
                    print(f"  🔍 Teste de extração SQL:")
                    
                    # Simulação dos json_extract
                    extractions = {
                        'id': payload.get('id'),
                        'data_criacao': payload.get('data_criacao'), 
                        'data_fechamento': payload.get('data_fechamento'),
                        'chamados': payload.get('chamados'),
                        'estado': payload.get('ordem_servico', {}).get('estado') if 'ordem_servico' in payload else None,
                        'numero': payload.get('ordem_servico', {}).get('numero') if 'ordem_servico' in payload else None
                    }
                    
                    for key, value in extractions.items():
                        if value is not None:
                            print(f"    - json_extract(payload, '$.{key}'): {value}")
                        else:
                            print(f"    - json_extract(payload, '$.{key}'): NULL")
                    
                except json.JSONDecodeError as e:
                    print(f"  ❌ JSON inválido: {e}")
                except Exception as e:
                    print(f"  ❌ Erro no parse: {e}")
            else:
                print(f"  ❌ Payload vazio")
                
        print(f"\n🔄 TESTANDO QUERY SQL REAL:")
        print("-" * 40)
        
        # Testar a query real
        with get_conn() as conn:
            test_df = pd.read_sql_query("""
                SELECT
                    json_extract(payload, '$.id') as id,
                    json_extract(payload, '$.chamados') as chamados,
                    json_extract(payload, '$.data_criacao') as data_criacao,
                    json_extract(payload, '$.data_fechamento') as data_fechamento,
                    json_extract(payload, '$.ordem_servico.estado') as estado,
                    json_extract(payload, '$.ordem_servico.numero') as numero,
                    created_at
                FROM orders
                ORDER BY created_at DESC
                LIMIT 5
            """, conn)
            
        print(f"📊 Registros retornados pela query: {len(test_df)}")
        
        for i, row in test_df.iterrows():
            print(f"\nLinha {i+1}:")
            print(f"  id: {row['id']}")
            print(f"  data_criacao: {row['data_criacao']} (tipo: {type(row['data_criacao'])})")
            print(f"  data_fechamento: {row['data_fechamento']}")
            print(f"  chamados: {row['chamados']}")
            print(f"  estado: {row['estado']}")
            print(f"  numero: {row['numero']}")
            print(f"  created_at: {row['created_at']}")
            
            # Testar conversão de data se não for None
            if row['data_criacao'] and row['data_criacao'] != 'None':
                try:
                    parsed_date = pd.to_datetime(row['data_criacao'])
                    print(f"  ✅ Data convertida: {parsed_date}")
                except Exception as e:
                    print(f"  ❌ Erro na conversão: {e}")
                    
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_recent_records()
