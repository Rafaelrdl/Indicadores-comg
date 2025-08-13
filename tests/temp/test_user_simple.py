from app.arkmeds_client.models import User

# Teste básico da classe User
try:
    u = User(id=123, nome="", email="")
    print(f"✅ User criado com ID: {u.id}")
    print(f"✅ Display name: '{u.display_name}'")
    print(f"✅ String repr: '{str(u)}'")
    print("🎉 Classe User funcionando perfeitamente!")
except Exception as e:
    print(f"❌ Erro na classe User: {e}")
    import traceback

    traceback.print_exc()
