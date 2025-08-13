#!/usr/bin/env python3

import sqlite3
import json

def investigate_sqlite_data():
    """Investiga os dados no banco SQLite."""
    print("🔍 INVESTIGAÇÃO DOS DADOS NO SQLITE")
    print("=" * 50)
    
    conn = sqlite3.connect('data/app.db')
    
    # 1. Verificar estrutura das tabelas
    print("\n📋 ESTRUTURA DAS TABELAS:")
    tables = ['orders', 'equipments', 'technicians', 'sync_state']
    for table in tables:
        try:
            cursor = conn.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"\n🔸 {table.upper()}:")
            for col in columns:
                print(f"   - {col[1]} ({col[2]})")
        except sqlite3.Error as e:
            print(f"   ❌ Erro ao verificar {table}: {e}")
    
    # 2. Contar registros
    print("\n📊 CONTAGEM DE REGISTROS:")
    for table in ['orders', 'equipments', 'technicians']:
        try:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   • {table}: {count:,} registros")
        except sqlite3.Error as e:
            print(f"   ❌ Erro ao contar {table}: {e}")
    
    # 3. Verificar dados de orders
    print("\n📋 AMOSTRA DOS DADOS (ORDERS):")
    try:
        cursor = conn.execute("SELECT id, payload FROM orders LIMIT 3")
        rows = cursor.fetchall()
        
        for i, row in enumerate(rows, 1):
            print(f"\n🔸 Record {i}:")
            print(f"   ID: {row[0]}")
            
            # Tentar extrair dados do payload
            try:
                payload = json.loads(row[1])
                data_criacao = payload.get('data_criacao', 'N/A')
                ordem_servico = payload.get('ordem_servico', {})
                estado = ordem_servico.get('estado', 'N/A') if isinstance(ordem_servico, dict) else 'N/A'
                
                print(f"   Data criação: {data_criacao}")
                print(f"   Estado: {estado}")
                print(f"   Payload size: {len(row[1])} chars")
            except json.JSONDecodeError:
                print(f"   ❌ Erro ao decodificar JSON")
                print(f"   Raw payload: {row[1][:100]}...")
                
    except sqlite3.Error as e:
        print(f"   ❌ Erro ao buscar orders: {e}")
    
    # 4. Verificar sync_state
    print("\n🔄 ESTADO DE SINCRONIZAÇÃO:")
    try:
        cursor = conn.execute("SELECT * FROM sync_state")
        rows = cursor.fetchall()
        
        for row in rows:
            print(f"   • Recurso: {row[0]}")
            print(f"     Última sync: {row[2]}")
            print(f"     Total registros: {row[3]}")
            print(f"     Tipo: {row[8] if len(row) > 8 else 'N/A'}")
            
    except sqlite3.Error as e:
        print(f"   ❌ Erro ao verificar sync_state: {e}")
    
    conn.close()
    print("\n✅ Investigação concluída!")

if __name__ == "__main__":
    investigate_sqlite_data()
