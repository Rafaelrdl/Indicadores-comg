#!/usr/bin/env python3
"""
Buscar registros com data_criacao no banco.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.db import get_conn
import json

def find_records_with_dates():
    """Buscar registros que tenham data_criacao."""
    print("🔍 BUSCANDO REGISTROS COM DATAS...")
    print("="*50)
    
    try:
        with get_conn() as conn:
            # Buscar registros que contenham 'data_criacao' no JSON
            cursor = conn.execute("""
                SELECT id, payload 
                FROM orders 
                WHERE payload LIKE '%data_criacao%' 
                LIMIT 5
            """)
            
            rows = cursor.fetchall()
            print(f"📊 Registros com 'data_criacao': {len(rows)}")
            
            if rows:
                for i, (record_id, payload) in enumerate(rows):
                    print(f"\n📋 REGISTRO {i+1} (ID: {record_id}):")
                    try:
                        data = json.loads(payload)
                        print(f"  data_criacao: {data.get('data_criacao')}")
                        print(f"  data_fechamento: {data.get('data_fechamento')}")
                    except:
                        print(f"  JSON inválido")
            else:
                print("❌ Nenhum registro encontrado com data_criacao")
                
                # Vamos ver se há outros campos de data
                print("\n🔍 Buscando outros padrões de data...")
                
                patterns = ['data_', 'date', 'created', 'updated']
                for pattern in patterns:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM orders WHERE payload LIKE '%{pattern}%'")
                    count = cursor.fetchone()[0]
                    print(f"  Registros com '{pattern}': {count}")
                    
                # Mostrar estrutura de um registro completo
                print("\n📋 ESTRUTURA DE UM REGISTRO COMPLETO:")
                cursor = conn.execute("SELECT payload FROM orders LIMIT 1")
                row = cursor.fetchone()
                if row:
                    try:
                        data = json.loads(row[0])
                        print("Campos disponíveis:", list(data.keys()))
                        print("JSON completo:")
                        print(json.dumps(data, indent=2, ensure_ascii=False)[:500] + "...")
                    except Exception as e:
                        print(f"Erro ao analisar JSON: {e}")
                        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    find_records_with_dates()
