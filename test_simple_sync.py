"""
Teste simples para verificar se o sistema de sync está funcionando.
"""
from app.core.db import init_database, get_conn
from app.services.sync._upsert import upsert_records

def test_basic_upsert():
    """Teste básico de upsert."""
    try:
        # Inicializar banco
        init_database()
        conn = get_conn()
        
        # Dados de teste
        test_records = [
            {
                'id': 99901,
                'chamados': 1001,
                'data_criacao': '2025-08-12T10:00:00',
                'updated_at': '2025-08-12T10:00:00'
            }
        ]
        
        # Fazer upsert
        count = upsert_records(conn, 'orders', test_records)
        print(f"✅ Upsert realizado: {count} registros")
        
        # Verificar se foi salvo
        cursor = conn.execute("SELECT COUNT(*) FROM orders WHERE id = 99901")
        result = cursor.fetchone()[0]
        print(f"✅ Registros encontrados: {result}")
        
        return count == 1 and result == 1
    
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

if __name__ == "__main__":
    success = test_basic_upsert()
    print(f"🎯 Teste {'passou' if success else 'falhou'}!")
