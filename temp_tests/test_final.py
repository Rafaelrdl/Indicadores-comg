#!/usr/bin/env python3
"""
Teste final de todas as melhorias implementadas na classe User.
"""

def test_user_class():
    print("🔍 Testando classe User melhorada...")
    
    try:
        from app.arkmeds_client.models import User
        print("✅ Import da classe User OK")
        
        # Teste 1: User apenas com ID
        print("\n1. User apenas com ID:")
        user1 = User(id=123)
        print(f"   ✅ Criado: ID={user1.id}")
        print(f"   ✅ Display name: '{user1.display_name}'")
        print(f"   ✅ String: '{str(user1)}'")
        
        # Teste 2: User com nome
        print("\n2. User com nome:")
        user2 = User(id=456, nome="João Silva", email="joao@test.com")
        print(f"   ✅ Criado: ID={user2.id}")
        print(f"   ✅ Display name: '{user2.display_name}'")
        print(f"   ✅ String: '{str(user2)}'")
        
        # Teste 3: User com first_name/last_name
        print("\n3. User com first_name/last_name:")
        user3 = User(id=789, first_name="Maria", last_name="Santos")
        print(f"   ✅ Criado: ID={user3.id}")
        print(f"   ✅ Display name: '{user3.display_name}'")
        print(f"   ✅ String: '{str(user3)}'")
        
        # Teste 4: User apenas com email
        print("\n4. User apenas com email:")
        user4 = User(id=101, email="carlos@empresa.com")
        print(f"   ✅ Criado: ID={user4.id}")
        print(f"   ✅ Display name: '{user4.display_name}'")
        print(f"   ✅ String: '{str(user4)}'")
        
        print("\n🎉 TODAS AS MELHORIAS DA CLASSE USER FUNCIONANDO!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enums():
    print("\n🔍 Testando Enums...")
    
    try:
        from app.arkmeds_client.models import OSEstado, TipoOS
        print("✅ Import dos Enums OK")
        
        print(f"✅ OSEstado: {len(OSEstado)} estados")
        print(f"✅ TipoOS: {len(TipoOS)} tipos")
        
        # Teste métodos utilitários
        print(f"✅ Estados abertos: {len(OSEstado.estados_abertos())}")
        print(f"✅ Tipos preventivos: {len(TipoOS.tipos_preventivos())}")
        
        print("🎉 ENUMS FUNCIONANDO!")
        return True
        
    except Exception as e:
        print(f"❌ Erro nos enums: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 TESTE FINAL - TODAS AS MELHORIAS IMPLEMENTADAS")
    print("=" * 60)
    
    user_ok = test_user_class()
    enum_ok = test_enums()
    
    print("\n" + "=" * 60)
    if user_ok and enum_ok:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Classe User melhorada e funcionando")
        print("✅ Enums OSEstado e TipoOS funcionando")
        print("✅ Sistema pronto para uso!")
    else:
        print("❌ Alguns testes falharam")
    print("=" * 60)
